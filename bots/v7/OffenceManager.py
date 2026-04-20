from cambc import *
import utils as U
import consts as C
from Nav import Nav
from Movement import Movement


class OffenceManager:
    def __init__(self, c: Controller):
        self.target = my_pos = c.get_position()
        my_team = c.get_team()

        self.candidate: tuple = ()
        building_id = c.get_tile_building_id(my_pos)
        if c.get_team(building_id) != my_team and c.get_entity_type(building_id) in C.CONVEYOR_VARIANT:
            blocked: list[bool] = [
                not U.on_the_map(pos := my_pos.add(d)) or c.get_tile_env(pos) == Environment.WALL for d in C.DIRECTIONS
            ]
            allow_set: dict[bool, EntityType] = {
                True: C.UNIMPORTANT | {EntityType.LAUNCHER},
                False: C.UNIMPORTANT
            }
            build_launcher: list[bool] = [
                U.on_the_map(pos := my_pos.add(d)) and c.get_tile_env(pos) != Environment.WALL and (
                            (building_id := c.get_tile_building_id(pos)) is None or c.get_entity_type(building_id) in
                            allow_set[c.get_team(building_id) == my_team]) for d in C.CARDINAL
            ]
            for i in range(4):
                if build_launcher[i]:
                    if build_launcher[(i + 2) % 4]:
                        self.candidate = (i, (i + 2) % 4)
                        break
                    if all(blocked[j % 8] for j in range(i * 2 + 3, i * 2 + 6)):
                        self.candidate = (i,)
                        break

    def update(self, c: Controller, nav: Nav, movement: Movement) -> bool:
        my_pos = c.get_position()

        if my_pos.distance_squared(self.target) > 8:
            nav.move(c, self.target, movement)
            return True

        my_team = c.get_team()

        for i in self.candidate:
            pos = self.target.add(C.CARDINAL[i])
            building_id = c.get_tile_building_id(pos)
            e_type = c.get_entity_type(building_id)
            if c.get_team(building_id) == my_team:
                if e_type == EntityType.LAUNCHER:
                    continue
                if building_id is None or e_type in C.UNIMPORTANT:
                    if c.can_destroy(pos):
                        c.destroy(pos)
                else:
                    return False
            else:
                if e_type == EntityType.ROAD:
                    movement.enrich(c)
                    nav.move(c, pos, movement)
                    my_pos = c.get_position()

                    if my_pos == pos:
                        if c.can_fire(my_pos):
                            c.fire(my_pos)
                            movement.act(c)
                    return True
                elif e_type != EntityType.MARKER:
                    return False
            nav.move(c, self.target, movement)
            my_pos = c.get_position()

            if c.can_build_launcher(pos):
                c.build_launcher(pos)
                movement.act(c)
            else:
                break
        else:
            if my_pos != self.target:
                nav.move(c, self.target, movement)
                my_pos = c.get_position()

            building_id = c.get_tile_building_id(self.target)
            if c.get_team(building_id) == my_team or c.get_entity_type(building_id) not in C.CONVEYOR_VARIANT:
                if c.can_build_road(self.target):
                    c.build_road(self.target)
                return False
            else:
                if c.can_fire(my_pos):
                    c.fire(my_pos)
                    movement.act(c)

        return True
