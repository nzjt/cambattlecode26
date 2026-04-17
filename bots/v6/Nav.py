from cambc import *
from Movement import Movement


class Nav:
    def move(self, c: Controller, target: Position, movement: Movement) -> None:
        self.multimove(c, [target], movement)

    def multimove(self, c: Controller, targets: list[Position] | int, movement: Movement, active: bool = False) -> None:
        pass
