from cambc import *
from AStarJPSOptimised import AStarJPSOptimised
from TileManager import TileManager
from Movement import Movement
from Bfs import Bfs
from consts import *


class ConveyorManager:
    def __init__(self, c: Controller, tile_manager: TileManager, start: Position, target: Position):
        W: int = c.get_map_width()
        self.on_path = [[False] * (W + 1) for _ in range(c.get_map_height() + 1)]

        a_star: AStarJPSOptimised = AStarJPSOptimised(tile_manager)
        a_star.compute(start, target, True)

        self.path: list[Position] = [start]
        path: list[Position] = self.path
        env_grid = tile_manager.env_grid
        for way_point in a_star.path:
            d: Direction = path[-1].direction_to(way_point)
            while path[-1] != way_point:
                dx, dy = d.delta()
                if dx and dy:
                    x, y = path[-1]
                    if env_grid[y][x + dx] == 1:
                        path.append(Position(x + dx, y))
                    elif env_grid[y + dy][x] == 1:
                        path.append(Position(x, y + dy))
                    path.append(Position(x + dx, y + dy))
                else:
                    path.append(path[-1].add(d))

        self.index = 1
        self.done: bool = False
        for i in range(1, len(path)):
            c.draw_indicator_line(path[i - 1], path[i], 255, 0, 255)

    def place(self, c: Controller, pos: Position) -> bool:
        if self.path[-1].distance_squared(pos) != 1:
            return False

        c.build_conveyor(pos, pos.direction_to(self.path[-1]))
        self.on_path[pos.y][pos.x] = True
        return True

    def update(self, c: Controller, movement: Movement, bfs_adj_exc):
        my_id = c.get_id()
        my_team = c.get_team()
        my_pos = c.get_position(my_id)

        print("yo")
        while self.index < len(self.path) - 1:
            pos: Position = self.path[self.index]
            if c.is_in_vision(pos):
                building_id = c.get_tile_building_id(pos)
                if building_id is None:
                    break
                if c.get_team(building_id) == my_team:
                    e_type = c.get_entity_type(building_id)
                    if e_type == EntityType.CONVEYOR:
                        if c.get_direction(building_id) == self.path[self.index].direction_to(self.path[self.index + 1]):
                            self.index += 1
                            continue
                    elif e_type == EntityType.BRIDGE:
                        if c.get_bridge_target(building_id) == self.path[self.index + 1]:
                            self.index += 1
                            continue
            break

        print("yo")
        if self.index == len(self.path) - 1:
            # Wow we're done
            pos: Position = self.path[0]

            if c.is_in_vision(pos):
                building_id = c.get_tile_building_id(pos)
                if building_id is None or c.get_entity_type(building_id) != EntityType.HARVESTER:
                    if c.get_global_resources()[0] < c.get_harvester_cost()[0]:
                        # Not enough money
                        return

                    if not 1 <= my_pos.distance_squared(pos) <= 2:
                        for d in CARDINAL:
                            if c.can_move(d):
                                if my_pos.add(d).distance_squared(pos) <= 2:
                                    movement.move(d)
                                    break
                        else:
                            # :(
                            return

                    if c.can_build_harvester(pos):
                        c.build_harvester(pos)
                        self.done = True
                else:
                    self.done = True
            else:
                # Probably built
                self.done = True
            return

        print("yo")
        do_build: bool = False
        if c.is_in_vision(self.path[0]):
            building_id = c.get_tile_building_id(self.path[0])
            do_build = building_id is None or c.get_entity_type(building_id) != EntityType.HARVESTER
        wealthy = c.get_global_resources()[0] >= c.get_harvester_cost()[0]

        pos: Position = self.path[self.index]
        if not c.get_move_cooldown() and (not do_build or wealthy):
            d: Direction = bfs_adj_exc(pos)
            if d != Direction.CENTRE:
                if c.can_move(d):
                    movement.move(d)
                else:
                    print("wtf!")
                my_pos = c.get_position(my_id)

        if do_build and wealthy and my_pos != self.path[0]:
            if c.can_destroy(self.path[0]):
                c.destroy(self.path[0])
            c.build_harvester(self.path[0])

        if my_pos.distance_squared(pos) <= 2:
            nxt = self.path[self.index + 1]
            d: Direction = pos.direction_to(nxt)
            building_id = c.get_tile_building_id(nxt)
            if building_id is None or c.get_team(building_id) == my_team:
                building_id = c.get_tile_building_id(pos)
                keep_gunner: bool = False
                if c.get_entity_type(building_id) == EntityType.GUNNER and c.get_team(building_id) == my_team:
                    di: Direction = c.get_direction(building_id)
                    cur: Position = pos
                    if di in CARDINAL:
                        for _ in range(3):
                            cur = cur.add(di)
                            building_id = c.get_tile_building_id(cur)
                            if building_id is not None:
                                keep_gunner = c.get_team() != my_team
                                break
                    else:
                        for _ in range(2):
                            cur = cur.add(di)
                            building_id = c.get_tile_building_id(cur)
                            if building_id is not None:
                                keep_gunner = c.get_team() != my_team
                                break

                if not keep_gunner:
                    if c.can_destroy(pos):
                        c.destroy(pos)

                    dx, dy = d.delta()
                    if dx and dy:
                        if c.can_build_bridge(pos, nxt):
                            c.build_bridge(pos, nxt)
                    else:
                        if c.can_build_conveyor(pos, d):
                            c.build_conveyor(pos, d)
            else:
                if c.can_build_gunner(pos, d):
                    c.build_gunner(pos, d)
