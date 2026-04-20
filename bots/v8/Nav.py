from cambc import *
from Movement import Movement


class Nav:
    def move(self, c: Controller, target: Position, movement: Movement, **kwargs) -> None:
        self.multimove(c, [target], movement, **kwargs)

    def multimove(self, c: Controller, targets: list[Position] | int, movement: Movement, **kwargs) -> None:
        pass
