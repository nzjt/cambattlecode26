import random

from cambc import *
from Unit import *
from consts import CONVEYOR_VARIANT


class Launcher(Unit):
    def run(self, c: Controller):
        my_pos = c.get_position()
        my_team = c.get_team()

        best: Position | None = None
        best_score: int = 0
        for building_id in c.get_nearby_buildings():
            pos = c.get_position(building_id)
            if c.is_tile_passable(pos):
                if c.get_entity_type(building_id) in CONVEYOR_VARIANT and c.get_team(building_id) == my_team:
                    continue

                dist = max(abs(pos.x - my_pos.x), abs(pos.y - my_pos.y))
                score = dist << 16 | random.randint(0, 0xFFFF)
                if score > best_score:
                    best = pos
                    best_score = score

        if best is None:
            return

        best_enemy: Position | None = None
        for bb_id in c.get_nearby_entities(2):
            if c.get_team(bb_id) == my_team:
                continue
            pos = c.get_position(bb_id)
            building_id = c.get_tile_building_id(pos)
            if c.can_launch(pos, best):
                if c.get_entity_type(building_id) in CONVEYOR_VARIANT and c.get_team(building_id) == my_team:
                    c.launch(pos, best)
                    return
                best_enemy = pos  # TODO

        if best_enemy is not None:
            c.launch(best_enemy, best)
