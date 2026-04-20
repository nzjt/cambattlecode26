from cambc import *
from TileManager import TileManager
from Movement import Movement
from consts import CARDINAL
from consts import UNIMPORTANT
from Bfs import Bfs
import utils as U


class FoundryManager:
    def __init__(self, home: Position, expiry: int):
        self.home: Position = home
        self.tracker: dict[Position, int] = {}
        self.target: Position = None
        self.sub_target: Position = None
        self.expiry: int = expiry

    def update(self, c: Controller, movement: Movement, tile_manager: TileManager, bfs: Bfs):
        if self.target is None:
            my_team = c.get_team()

            for building_id in c.get_nearby_buildings(13):
                if c.get_entity_type(building_id) == EntityType.CONVEYOR:
                    # Check space
                    d: Direction = c.get_direction(building_id)
                    pos: Position = c.get_position(building_id)
                    if pos.add(d).distance_squared(self.home) <= 2:
                        resource: ResourceType = c.get_stored_resource(building_id)
                        left_good: bool = False
                        nxt = pos.add(d.rotate_left().rotate_left())
                        if nxt.distance_squared(self.home) <= 5:
                            if U.on_the_map(nxt):
                                building_id = c.get_tile_building_id(nxt)
                                left_good |= building_id is None or (c.get_entity_type(building_id) in UNIMPORTANT and c.get_team(building_id) == my_team)
                        right_good: bool = False
                        nxt = pos.add(d.rotate_right().rotate_right())
                        if nxt.distance_squared(self.home) <= 5:
                            if U.on_the_map(nxt):
                                building_id = c.get_tile_building_id(nxt)
                                right_good |= building_id is None or (c.get_entity_type(building_id) in UNIMPORTANT and c.get_team(building_id) == my_team)

                        if left_good or right_good:
                            val: int = self.tracker.get(pos, 0)
                            if resource == ResourceType.TITANIUM:
                                val |= 1
                            elif resource == ResourceType.RAW_AXIONITE:
                                val |= 2
                            if val == 3:
                                self.target = pos
                                self.sub_target = pos.add(d.rotate_left().rotate_left()) if left_good else pos.add(d.rotate_right().rotate_right())

                            self.tracker[pos] = val
                        else:
                            self.tracker[pos] = 0

        if self.target is not None:
            building_id = c.get_tile_building_id(self.target)
            my_pos = c.get_position()
            if c.get_entity_type(building_id) == EntityType.CONVEYOR:
                if my_pos.distance_squared(self.target) > 2:
                    d: Direction = bfs.bfs_adj_exc(self.target.x - my_pos.x, self.target.y - my_pos.y, tile_manager.pass_)
                    if d is not None and d != Direction.CENTRE and movement.can_move(d):
                        movement.move(d)
                        my_pos = c.get_position()

                if my_pos.distance_squared(self.target) <= 2:
                    if c.get_global_resources()[0] >= c.get_splitter_cost()[0]:
                        c.destroy(self.target)
                        for d in CARDINAL:
                            nxt = self.target.add(d)
                            building_id = c.get_tile_building_id(nxt)
                            if c.get_entity_type(building_id) == EntityType.CONVEYOR:
                                if nxt.add(c.get_direction(building_id)) == self.target:
                                    c.build_splitter(self.target, d.opposite())
                                    break
                        else:
                            return
                    else:
                        return
                else:
                    return

            if my_pos.distance_squared(self.sub_target) > 2:
                d: Direction = bfs.bfs_adj_exc(self.sub_target.x - my_pos.x, self.sub_target.y - my_pos.y, tile_manager.pass_)
                if d is not None and d != Direction.CENTRE and movement.can_move(d):
                    movement.move(d)
                    my_pos = c.get_position()

            if my_pos.distance_squared(self.sub_target) <= 2:
                if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_foundry_cost()[0]:
                    if c.can_destroy(self.sub_target):
                        c.destroy(self.sub_target)
                    if c.can_build_foundry(self.sub_target):
                        c.build_foundry(self.sub_target)

    @staticmethod
    def check_foundry(c: Controller) -> bool:
        for building_id in c.get_nearby_buildings(13):
            if c.get_entity_type(building_id) == EntityType.FOUNDRY:
                return True
        return False
