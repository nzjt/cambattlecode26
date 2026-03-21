from cambc import *
from Unit import Unit
from consts import *


class Sentinel(Unit):
    def run(self, c: Controller):
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
                for d in CARDINAL:
                    nxt = pos.add(d)
                    if 0 <= nxt.x < W and 0 <= nxt.y < H and c.can_fire(nxt):
                        building_id = c.get_tile_building_id(nxt)
                        if c.get_entity_type(building_id) in CONVEYOR_VARIANT and c.get_team(building_id) != my_team:
                            if score < 4:
                                best = nxt
                                score = 4
                                break
            else:
                if c.get_team(e_id) == my_team:
                    continue

                if e_type == EntityType.CORE:
                    for d in Direction:
                        nxt = pos.add(d)
                        if c.can_fire(nxt):
                            if score < 3:
                                best = nxt
                                score = 3
                                break
                elif e_type == EntityType.ROAD:
                    if c.can_fire(pos):
                        if score < 1:
                            best = pos
                            score = 1
                elif e_type != EntityType.BUILDER_BOT:
                    if c.can_fire(pos):
                        if score < 2:
                            best = pos
                            score = 2

        if best is None:
            pass # destruct
        else:
            c.fire(best)
