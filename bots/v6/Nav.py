from cambc import *
from Movement import Movement


class Nav:
    def move(self, c: Controller, target: Position, movement: Movement) -> None:
        pass

    def multimove(self, c: Controller, targets: list[Position], movement: Movement) -> None:
        pass
