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
            self.prev = None

        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        opt: Direction = my_pos.direction_to(target)

        if opt == Direction.CENTRE:
            return

        if self.prev is not None:
            if self.turn:
                d = self.prev.rotate_right().rotate_right()
                if movement.can_move(d.rotate_right()):
                    self.prev = None
            else:
                d = self.prev.rotate_left().rotate_left()
                if movement.can_move(d.rotate_left()):
                    self.prev = None

        if self.prev is None:
            d = opt

        dist = my_pos.distance_squared(target)

        if movement.can_move(opt):
            if self.prev is None:
                movement.move(opt)
                return
            elif dist < self.dist:
                movement.move(opt)
                self.turn = None
                return
        elif self.prev is None:
            self.turn = bool(random.randint(0, 1))
            self.dist = dist

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
