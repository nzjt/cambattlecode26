from cambc import *
from AStarJPSOptimised import AStarJPSOptimised
from TileManager import TileManager
from Movement import Movement
from Bfs import Bfs
from consts import *


class ConveyorManager:
    def __init__(self, c: Controller, tile_manager: TileManager, start: Position, target: Position):
        W: int = c.get_map_width()

        a_star: AStarJPSOptimised = AStarJPSOptimised(tile_manager)
        a_star.compute(start, [target], True)

        path = self.path = ConveyorManager.normalise(a_star.path, tile_manager.env_grid)

        self.path_index: list[list[int]] = [[1000000] * (W + 1) for _ in range(c.get_map_height() + 1)]
        path_index = self.path_index
        for i in range(len(path)):
            x, y = path[i]
            path_index[y][x] = i

        self.index = 1
        self.done: bool = False
        for i in range(1, len(path)):
            c.draw_indicator_line(path[i - 1], path[i], 255, 0, 255)

    @staticmethod
    def normalise(waypoints: list[Position], env_grid: list[list[int]]):
        path: list[Position] = [waypoints[0]]
        for way_point in waypoints:
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
        return path

    def place(self, c: Controller, pos: Position) -> bool:
        if self.path[-1].distance_squared(pos) != 1:
            return False

        c.build_conveyor(pos, pos.direction_to(self.path[-1]))
        self.path_index[pos.y][pos.x] = True
        return True

    def retarget(self, c: Controller, retargets: list[Position], tile_manager: TileManager):
        x, y = c.get_position()
        lo, hi = self.index, self.index
        xi, yi = self.path[hi]
        dx, dy = xi - x, yi - y
        goal: int = 1 << (dx + dy * 10 + 44)

        while lo > 1:
            xi, yi = self.path[lo - 1]
            dx, dy = xi - x, yi - y
            if -4 <= dx <= 4 and -4 <= dy <= 4:
                goal |= 1 << (dx + dy * 10 + 44)
                lo -= 1
            else:
                break

        retarget_set: int = 0
        for xi, yi in retargets:
            dx, dy = xi - x, yi - y
            if -4 <= dx <= 4 and -4 <= dy <= 4:
                retarget_set |= 1 << (dx + dy * 10 + 44)

        raw_path: list[tuple[int, int]] = Bfs.closest_start(goal, retarget_set, (tile_manager.pass_ | tile_manager.buildable) & ~tile_manager.ore)
        if not raw_path:
            return

        suffix: list[Position] = [Position(x + dx, y + dy) for dx, dy in raw_path]
        suffix = ConveyorManager.normalise(suffix, tile_manager.env_grid)
        if len(suffix) < len(self.path) - self.index:
            while self.path[self.index] != suffix[0]:
                self.index -= 1
            self.path = self.path[:self.index]

            self.path += suffix

            for i in range(1, len(self.path)):
                c.draw_indicator_line(self.path[i - 1], self.path[i], 255, 255, 0)

    def update_index(self, c: Controller):
        my_team = c.get_team()

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

    def update(self, c: Controller, movement: Movement, tile_manager: TileManager, bfs: Bfs):
        my_id = c.get_id()
        my_team = c.get_team()
        my_pos = c.get_position(my_id)

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
                        d: Direction = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, tile_manager.pass_)
                        if d is None:
                            # :(
                            pass
                        elif c.can_move(d):
                            movement.move(d)

                    if c.can_destroy(pos):
                        c.destroy(pos)

                    if c.can_build_harvester(pos):
                        c.build_harvester(pos)
                        self.done = True
                else:
                    self.done = True
            else:
                # Probably built
                self.done = True
            return

        do_build: bool = False
        if c.is_in_vision(self.path[0]):
            building_id = c.get_tile_building_id(self.path[0])
            do_build = building_id is None or c.get_entity_type(building_id) != EntityType.HARVESTER
        wealthy = c.get_global_resources()[0] >= c.get_harvester_cost()[0]

        pos: Position = self.path[self.index]
        nxt = self.path[self.index + 1]
        need_gunner = c.is_in_vision(nxt) and c.get_team(c.get_tile_building_id(nxt)) != my_team
        if not c.get_move_cooldown() and (not do_build or wealthy):
            pass_: int = tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy
            if need_gunner:
                d: Direction = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
            else:
                d: Direction = bfs.bfs_to_pos(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
                if d is None or d != Direction.CENTRE and not c.can_move(d):
                    d = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
            if d is None:
                # Can't reach => done?
                self.done = True
                return
            elif d != Direction.CENTRE:
                if c.can_move(d):
                    movement.move(d)
                else:
                    print("wtf!", d)
                my_pos = c.get_position(my_id)

        if do_build and wealthy and my_pos != self.path[0]:
            if c.can_destroy(self.path[0]):
                c.destroy(self.path[0])
            c.build_harvester(self.path[0])

        if my_pos.distance_squared(pos) <= 2:
            d: Direction = pos.direction_to(nxt)
            building_id = c.get_tile_building_id(pos)
            if need_gunner:
                if c.get_entity_type(building_id) != EntityType.GUNNER and c.can_destroy(pos):
                    c.destroy(pos)

                if c.can_build_gunner(pos, d):
                    c.build_gunner(pos, d)
            else:
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

                if not keep_gunner and not c.get_action_cooldown():
                    if c.can_destroy(pos):
                        c.destroy(pos)

                    dx, dy = d.delta()
                    if dx and dy:
                        if c.can_build_bridge(pos, nxt):
                            c.build_bridge(pos, nxt)
                    else:
                        if c.can_build_conveyor(pos, d):
                            c.build_conveyor(pos, d)
