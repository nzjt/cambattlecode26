from cambc import *
from Unit import Unit


class Core(Unit):
    def run(self, c: Controller):
        my_pos = c.get_position(c.get_id())

        if c.get_current_round() <= 5 or c.get_current_round() == 150:
            for d in Direction:
                pos = my_pos.add(d)
                if c.can_spawn(pos):
                    c.spawn_builder(pos)
                    break
