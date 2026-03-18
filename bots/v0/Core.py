from cambc import *
from Unit import Unit


class Core(Unit):
    def run(self, c: Controller):
        if c.get_current_round() == 0:
            c.spawn_builder(c.get_position(c.get_id()))
