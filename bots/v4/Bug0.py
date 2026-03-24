from cambc import *
from Nav import Nav
import random
from Movement import Movement


class Bug0(Nav):
    def __init__(self):
        self.target: Position | None = None
        self.turn: bool | None = None

    def move_(self, c: Controller, target: Position, movement: Movement) -> None:
        if c.get_move_cooldown():
            return

        if target != self.target:
            self.target = target

        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        d: Direction = my_pos.direction_to(target)

        if d == Direction.CENTRE:
            return

        if movement.can_move(d):
            movement.move_(d)
            self.turn = None
        else:
            if self.turn is None:
                self.turn = bool(random.randint(0, 1))

            if self.turn:
                # Left turning
                for _ in range(7):
                    d = d.rotate_left()
                    if movement.can_move(d):
                        movement.move_(d)
                        return
            else:
                # Right turning
                for _ in range(7):
                    d = d.rotate_right()
                    if movement.can_move(d):
                        movement.move_(d)
                        return
