from cambc import *
from Unit import Unit


class Core(Unit):
    def run(self, c: Controller):
        my_pos = c.get_position(c.get_id())

        if c.get_current_round() <= 5:
            for d in Direction:
                pos = my_pos.add(d)
                if c.can_spawn(pos):
                    c.spawn_builder(pos)
                    break
        elif c.get_global_resources()[0] / c.get_scale_percent() >= 3:
            for d in Direction:
                pos = my_pos.add(d)
                if c.can_spawn(pos):
                    c.spawn_builder(pos)
                    break
