import random
from cambc import *


class SpawnManager:
    def __init__(self):
        self.spawned: int = 0

    def spawn(self, c: Controller) -> bool:
        my_pos = c.get_position()
        directions = list(Direction)
        random.shuffle(directions)
        for d in directions:
            pos = my_pos.add(d)
            if c.can_spawn(pos):
                c.spawn_builder(pos)
                self.spawned += 1
                return True

        return False
