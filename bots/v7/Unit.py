import sys
from cambc import *
import consts as C
import utils as U


class Unit:
    def __init__(self, c: Controller):
        C.W = c.get_map_width()
        C.H = c.get_map_height()
        U.on_the_map = lambda pos, W = C.W, H = C.H: 0 <= pos.x < W and 0 <= pos.y < H
        map_mask: int = (1 << C.W) - 1
        for _ in range(C.H - 1):
            map_mask |= map_mask << (C.W + 1)
        C.MAP_MASK = map_mask

    def run(self, c: Controller):
        U.debug = lambda msg, my_id = f"{c.get_id()}{c.get_team().name}", c = c, round = c.get_current_round(): print(f"[{my_id}@{tuple(c.get_position())}@{round}] {msg}", file=sys.stderr)
        U.is_visible = lambda pos, W = C.W, H = C.H, c = c: 0 <= pos.x < W and 0 <= pos.y < H and c.is_in_vision(pos)
