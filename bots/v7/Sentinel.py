from cambc import *
from Unit import Unit
import consts as C
import utils as U


class Sentinel(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)

    def run(self, c: Controller):
        super().run(c)
        if c.get_action_cooldown():
            return

        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        W, H = c.get_map_width(), c.get_map_height()

        best: Position | None = None
        score = 0
        for e_id in c.get_nearby_entities():
            e_type = c.get_entity_type(e_id)
            pos = c.get_position(e_id)
            if e_type == EntityType.HARVESTER:
                env: Environment = c.get_tile_env(pos)
                if env == Environment.ORE_TITANIUM:
                    for d in C.CARDINAL:
                        nxt = pos.add(d)
                        if U.on_the_map(nxt) and c.can_fire(nxt):
                            building_id = c.get_tile_building_id(nxt)
                            if c.get_entity_type(building_id) in C.CONVEYOR_VARIANT and c.get_team(building_id) != my_team:
                                if score < 9:
                                    best = nxt
                                    score = 9
                                    break
                    if c.get_team(building_id) != my_team:
                        if c.can_fire(pos):
                            if score < 7:
                                best = pos
                                score = 7
                elif env == Environment.ORE_AXIONITE:
                    if c.get_team(building_id) != my_team:
                        if c.can_fire(pos):
                            if score < 6:
                                best = pos
                                score = 6
            else:
                if c.get_team(e_id) == my_team:
                    continue

                if e_type == EntityType.CORE:
                    for d in Direction:
                        nxt = pos.add(d)
                        if c.can_fire(nxt):
                            if score < 4:
                                best = nxt
                                score = 4
                                break
                elif c.can_fire(pos):
                    if e_type == EntityType.ROAD:
                        if score < 1:
                            best = pos
                            score = 1
                    elif e_type in C.TURRET:
                        if score < 8:
                            best = pos
                            score = 8
                    elif e_type == EntityType.BUILDER_BOT:
                        building_id = c.get_tile_building_id(pos)
                        if building_id is None or c.get_team(building_id) != my_team or c.get_entity_type(building_id) in C.UNIMPORTANT:
                            if score < 3:
                                best = pos
                                score = 3
                    elif e_type == EntityType.FOUNDRY:
                        if score < 5:
                            best = pos
                            score = 5
                    else:
                        if score < 2:
                            best = pos
                            score = 2

        if best is None:
            pass # destruct
        else:
            c.fire(best)
