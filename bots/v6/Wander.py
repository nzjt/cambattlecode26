from cambc import *
from Nav import Nav
from Movement import Movement


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
            for pos in self.unseen:
                c.draw_indicator_dot(pos, 0, 255, 0)
            self.nav.multimove(c, list(self.unseen), self.movement, True)
