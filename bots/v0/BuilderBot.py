from cambc import *
from Unit import Unit
from Movement import Movement
from Nav import Nav
from Bug0Better import Bug0Better


class BuilderBot(Unit):
    def __init__(self):
        self.movement: Movement | None = None
        self.nav: Nav = Bug0Better()

    def run(self, c: Controller):
        if self.movement is None:
            self.movement = Movement(c)

        self.nav.move(c, Position(46, 46), self.movement)
