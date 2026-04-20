from cambc import *
from TileManager import TileManager
import random
import consts as C


class ExplorationManager:
    def __init__(self):
        self.queue: list[Position] = []

    def enqueue(self, pos: Position):
        if pos not in self.queue:
            self.queue.append(pos)

    def get_target(self, c: Controller, tile_manager: TileManager):
        if self.queue:
            return self.queue.pop(0)

        W_minus_1, H_minus_1 = C.W - 1, C.H - 1
        for _ in range(10):
            target = Position(random.randint(0, W_minus_1), random.randint(0, H_minus_1))
            if not c.is_in_vision(target) and tile_manager.pass_grid[target.y][target.x]:
                return target
        return None
