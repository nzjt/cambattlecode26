from cambc import *
from Unit import Unit
import consts as C
import utils as U


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
            do_fire: bool = False
            actual_target = None
            target = my_pos
            for _ in range(3 if d in C.CARDINAL else 2):
                target = target.add(d)
                if U.on_the_map(target) and c.get_tile_env(target) != Environment.WALL:
                    bb_id = c.get_tile_builder_bot_id(target)
                    if bb_id is not None:
                        if c.get_team(bb_id) != my_team:
                            if actual_target is None:
                                actual_target = target
                            do_fire = True
                        break

                    building_id = c.get_tile_building_id(target)
                    if building_id is not None:
                        e_type = c.get_entity_type(building_id)
                        if c.get_team(building_id) == my_team:
                            if e_type == EntityType.ROAD:
                                if actual_target is None:
                                    actual_target = target
                            elif e_type != EntityType.MARKER:
                                break
                        else:
                            if c.get_entity_type(building_id) != EntityType.MARKER:
                                if actual_target is None:
                                    actual_target = target
                                do_fire = True
                                break
                else:
                    break

            if do_fire:
                c.fire(actual_target)
                return

        target = my_pos
        useful: bool = False
        for _ in range(3 if d in C.CARDINAL else 2):
            target = target.add(d)
            if U.on_the_map(target) and c.get_tile_env(target) != Environment.WALL:
                building_id = c.get_tile_building_id(target)
                if building_id is not None and c.get_entity_type(building_id) != EntityType.MARKER:
                    useful = c.get_team(building_id) != my_team
                    break
            else:
                break

        if not useful:
            for d in C.DIRECTIONS:
                target = my_pos
                for _ in range(3 if d in C.CARDINAL else 2):
                    target = target.add(d)
                    if U.on_the_map(target) and c.get_tile_env(target) != Environment.WALL:
                        building_id = c.get_tile_building_id(target)
                        if building_id is not None:
                            if c.get_team(building_id) == my_team:
                                break
                            elif c.get_entity_type(building_id) not in C.UNIMPORTANT:
                                if c.can_rotate(d):
                                    c.rotate(d)
                                return
                    else:
                        break
            c.self_destruct()
