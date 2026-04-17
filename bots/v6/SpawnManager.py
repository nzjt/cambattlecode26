import random
from cambc import *
import consts as C


class SpawnManager:
    def __init__(self):
        self.spawned: int = 0
        self.queue: list[Position] = []

    def spawn(self, c: Controller) -> bool:
        if self.queue:
            pos: Position = self.queue[0]
            if c.can_spawn(pos):
                c.spawn_builder(pos)
                self.spawned += 1
                self.queue.pop(0)
            return True

        my_pos = c.get_position()
        directions = list(C.DIRECTIONS)
        random.shuffle(directions)
        for d in directions:
            pos = my_pos.add(d)
            if c.can_spawn(pos):
                c.spawn_builder(pos)
                self.spawned += 1
                return True

        return False
