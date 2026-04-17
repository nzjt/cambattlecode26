from cambc import *
from Nav import Nav
from Movement import Movement


class StalkerManager:
    def __init__(self):
        self.targets: dict[int, Position] = {}

    def cleanse(self, c: Controller):
        my_pos: Position = c.get_position()

        rem = []
        for id_, pos in self.targets.items():
            if pos.distance_squared(my_pos) <= 2:
                if c.get_tile_builder_bot_id(pos) != id_:
                    rem.append(id_)
        for id_ in rem:
            self.targets.pop(id_)

    def update(self, c: Controller, nav: Nav, movement: Movement):
        print(self.targets)
        nav.multimove(c, list(self.targets.values()), movement, adj=True, active=True)
