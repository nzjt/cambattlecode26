from cambc import *
from Unit import Unit
import consts as C


class Gunner(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)

    def run(self, c: Controller):
        super().run(c)

        if c.get_action_cooldown():
            return

        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        d = c.get_direction(my_id)

        if c.get_ammo_amount():
            target = my_pos
            for _ in range(3):
                target = target.add(d)
                bb_id = c.get_tile_builder_bot_id(target)
                if bb_id is not None:
                    if c.get_team(bb_id) == my_team:
                        break
                    else:
                        c.fire(target)
                        return

                building_id = c.get_tile_building_id(target)
                if building_id is not None and c.get_entity_type(building_id) != EntityType.MARKER:
                    if c.get_team(building_id) == my_team:
                        break

                    c.fire(target)
                    break

        if c.get_action_cooldown():
            return

        target = my_pos
        useful: bool = False
        for _ in range(3 if d in C.CARDINAL else 2):
            target = target.add(d)
            building_id = c.get_tile_building_id(target)
            if building_id is not None:
                if c.get_team(building_id) == my_team:
                    break
                else:
                    useful = True
                    break

        if not useful:
            for d in C.DIRECTIONS:
                target = my_pos
                for _ in range(3 if d in C.CARDINAL else 2):
                    target = target.add(d)
                    building_id = c.get_tile_building_id(target)
                    if building_id is not None:
                        if c.get_team(building_id) == my_team:
                            break
                        elif c.get_entity_type(building_id) not in C.UNIMPORTANT:
                            c.rotate(d)
                            return
