from cambc import *
from Unit import Unit
from consts import UNIMPORTANT


class Gunner(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)

    def run(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        d = c.get_direction(my_id)

        target = my_pos
        for _ in range(3):
            target = target.add(d)
            if c.can_fire(target):
                building_id = c.get_tile_building_id(target)
                if building_id is not None and c.get_team(building_id) == my_team:
                    if c.get_entity_type(building_id) in UNIMPORTANT:
                        bb_id = c.get_tile_builder_bot_id(target)
                        if c.get_team(bb_id) == my_team:
                            break
                    else:
                        break

                bb_id = c.get_tile_builder_bot_id(target)
                if bb_id is not None and c.get_team(bb_id) == my_team:
                    break

                c.fire(target)
                break
