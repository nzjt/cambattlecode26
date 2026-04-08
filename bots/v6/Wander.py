from cambc import *
from Nav import Nav
from Movement import Movement
import consts as C


class Wander:
    def __init__(self, nav: Nav, movement: Movement):
        self.nav: Nav = nav
        self.movement: Movement = movement
        self.seen: set[Position] = set()
        self.unseen: set[Position] = set()

    def update(self, c: Controller):
        if not self.unseen:
            self.unseen, self.seen = self.seen, self.unseen

        if self.unseen:
            CONVEYOR_VARIANT = C.CONVEYOR_VARIANT
            my_team = c.get_team()
            is_in_vision = c.is_in_vision
            get_entity_type = c.get_entity_type
            get_tile_building_id = c.get_tile_building_id
            get_team = c.get_team
            for pos in [
                pos for pos in self.unseen if is_in_vision(pos) and (get_entity_type(building_id := get_tile_building_id(pos)) not in CONVEYOR_VARIANT or get_team(building_id) != my_team)
            ]:
                self.unseen.remove(pos)
            for pos in self.unseen:
                c.draw_indicator_dot(pos, 0, 255, 0)
            self.nav.multimove(c, list(self.unseen), self.movement, True)
