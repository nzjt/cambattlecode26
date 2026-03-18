from cambc import *


class TileManager:
    def __init__(self, c: Controller):
        W: int = c.get_map_width()
        H: int = c.get_map_height()
        self.pass_ = [0] * H
        self.allies: int = 0
        self.enemies: int = 0
        self.build_harvester = [[True] * W for _ in range(H)]

    def sense(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        for pos in c.get_nearby_tiles():
            building_id = c.get_tile_building_id(pos)
            if building_id is None:
                if c.get_tile_env(pos) != Environment.WALL:
                    self.pass_[pos.y] |= 1 << pos.x
            elif c.get_team(building_id) == my_team:
                e_type = c.get_entity_type(building_id)
                if e_type == EntityType.ROAD or e_type == EntityType.CORE:
                    self.pass_[pos.y] |= 1 << pos.x
            else:
                e_type = c.get_entity_type(building_id)
                if e_type == EntityType.ROAD:
                    self.pass_[pos.y] |= 1 << pos.x
            bb_id = c.get_tile_builder_bot_id(pos)
            if bb_id is not None:
                team = c.get_team(bb_id)
                dx = pos.x - my_pos.x
                dy = pos.y - my_pos.y
                if team == my_team:
                    self.allies |= 1 << (dx + dy * 10 + 44)
                else:
                    self.enemies |= 1 << (dx + dy * 10 + 44)