from cambc import *
import consts as C
import utils as U


class Unit:
    def __init__(self, c: Controller):
        C.W = c.get_map_width()
        C.H = c.get_map_height()
        U.on_the_map = lambda pos, W = C.W, H = C.H: 0 <= pos.x < W and 0 <= pos.y < H

    def run(self, c: Controller):
        pass
