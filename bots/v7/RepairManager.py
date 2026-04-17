from cambc import *
from Nav import Nav


class RepairManager:
    def __init__(self, nav: Nav):
        self.queue: list[tuple[Position, tuple]] = []
        self.nav: Nav = nav

    def add(self, pos: Position, building: tuple):
        self.queue.append((pos, building))

    def update(self, c: Controller):
        pass
