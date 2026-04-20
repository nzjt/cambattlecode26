from cambc import *
from Nav import Nav
from Movement import Movement
import consts as C


class Wander:
    def __init__(self, nav: Nav, movement: Movement):
        self.nav: Nav = nav
        self.movement: Movement = movement
        self.seen: int = 0

    def update(self, c: Controller, ever_seen: int):
        if self.seen == ever_seen:
            self.seen = 0

        if ever_seen ^ self.seen:
            self.nav.multimove(c, ever_seen ^ self.seen, self.movement, active=True)

    def forget(self):
        self.seen = 0
