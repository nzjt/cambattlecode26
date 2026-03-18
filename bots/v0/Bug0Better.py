from cambc import *
from Nav import Nav
import random
from Movement import Movement


class Bug0Better(Nav):
    def __init__(self):
        self.target: Position | None = None
        self.turn: bool | None = None
        self.dist: int = 0
        self.prev: Direction | None = None

    def move(self, c: Controller, target: Position, movement: Movement) -> None:
        if c.get_move_cooldown():
            return

        if target != self.target:
            self.target = target
            self.turn = None

        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        d: Direction = my_pos.direction_to(target)

        if d == Direction.CENTRE:
            return

        dist = my_pos.distance_squared(target)

        if movement.can_move(d):
            if self.turn is None:
                movement.move(d)
                return
            elif dist < self.dist:
                movement.move(d)
                self.turn = None
                return
        elif self.turn is None:
            self.turn = bool(random.randint(0, 1))
            self.dist = dist
            self.prev = None

        if self.prev is not None:
            if self.turn:
                d = self.prev.rotate_right().rotate_right()
            else:
                d = self.prev.rotate_left().rotate_left()

        if self.turn:
            # Left turning
            for _ in range(8):
                if movement.can_move(d):
                    movement.move(d)
                    self.prev = d
                    return
                d = d.rotate_left()
        else:
            # Right turning
            for _ in range(8):
                if movement.can_move(d):
                    movement.move(d)
                    self.prev = d
                    return
                d = d.rotate_right()
