from cambc import *
from AStarJPSOptimised import AStarJPSOptimised
from TileManager import TileManager
from Movement import Movement
from Nav import Nav
from consts import  *


class ConveyorManager:
    def __init__(self, c: Controller, tile_manager: TileManager, start: Position, target: Position):
        W: int = c.get_map_width()
        self.on_path = [[False] * (W + 1) for _ in range(c.get_map_height() + 1)]

        a_star: AStarJPSOptimised = AStarJPSOptimised(tile_manager)
        a_star.compute(start, target)

        self.path: list[Position] = [start]
        path: list[Position] = self.path
        for way_point in a_star.path:
            d: Direction = path[-1].direction_to(way_point)
            while path[-1] != way_point:
                path.append(path[-1].add(d))

        self.index = 1
        self.done: bool = False

    def place(self, c: Controller, pos: Position) -> bool:
        if self.path[-1].distance_squared(pos) != 1:
            return False

        c.build_conveyor(pos, pos.direction_to(self.path[-1]))
        self.on_path[pos.y][pos.x] = True
        return True

    def update(self, c: Controller, movement: Movement, nav: Nav):
        my_id = c.get_id()
        my_team = c.get_team()
        my_pos = c.get_position(my_id)

        while self.index < len(self.path) - 1:
            pos: Position = self.path[self.index]
            if c.is_in_vision(pos):
                building_id = c.get_tile_building_id(pos)
                if building_id is None:
                    break
                if c.get_entity_type(building_id) == EntityType.CONVEYOR and c.get_team(building_id) == my_team:
                    self.index += 1
                    continue
            break

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
                # Probably built
                self.done = True
            return

        do_build: bool = False
        if c.is_in_vision(self.path[0]):
            building_id = c.get_tile_building_id(self.path[0])
            do_build = building_id is None or c.get_entity_type(building_id) != EntityType.HARVESTER
        wealthy = c.get_global_resources()[0] >= c.get_harvester_cost()[0]

        pos: Position = self.path[self.index]
        if not do_build or wealthy:
            nav.move(c, pos, movement)

        if do_build and wealthy:
            if c.can_destroy(self.path[0]):
                c.destroy(self.path[0])
            c.build_harvester(self.path[0])

        d: Direction = pos.direction_to(self.path[self.index + 1])
        if c.can_destroy(pos):
            c.destroy(pos)
        if c.can_build_conveyor(pos, d):
            c.build_conveyor(pos, d)
