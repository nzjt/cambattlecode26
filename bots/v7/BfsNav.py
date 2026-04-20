import random
from cambc import *
from Nav import Nav
from Movement import Movement
from TileManager import TileManager
from itertools import chain, batched
import consts as C


class BfsNav(Nav):
    def __init__(self, home: Position, tile_manager: TileManager):
        self.home: Position = home
        self.tile_manager: TileManager = tile_manager

    def multimove(self, c: Controller, targets: list[Position] | int, movement: Movement, **kwargs) -> bool:
        W_plus_1: int = C.W + 1
        target: int = targets if isinstance(targets, int) else sum(
            1 << (y * W_plus_1 + x) for x, y in targets
        )
        if kwargs.get("adj", False):
            if kwargs.get("exc", False):
                centre: int = target
                target |= target << 1 | target >> 1
                target |= target << W_plus_1 | target >> W_plus_1
                target &= ~centre
            else:
                target |= target << 1 | target >> 1
                target |= target << W_plus_1 | target >> W_plus_1
        not_unit: int = ~self.tile_manager["unit"]

        x, y = c.get_position()
        me: int = 1 << (y * W_plus_1 + x)

        active: bool = kwargs.get("active", False)
        if not active:
            if target & me:
                # Already at target
                return True

        adj = me | me << 1 | me >> 1
        adj |= adj << W_plus_1 | adj >> W_plus_1

        hx, hy = self.home
        if ((x - hx) ^ (y - hy)) & 1:
            def move(adj: int) -> bool:
                options: list[Direction] = []
                if adj & (me >> W_plus_1):
                    if movement.can_move(Direction.NORTH):
                        options.append(Direction.NORTH)
                if adj & (me >> 1):
                    if movement.can_move(Direction.WEST):
                        options.append(Direction.WEST)
                if adj & (me << 1):
                    if movement.can_move(Direction.EAST):
                        options.append(Direction.EAST)
                if adj & (me << W_plus_1):
                    if movement.can_move(Direction.SOUTH):
                        options.append(Direction.SOUTH)

                if options:
                    movement.move(random.choice(options))
                    return True

                if adj & (me >> (W_plus_1 + 1)):
                    if movement.can_move(Direction.NORTHWEST):
                        options.append(Direction.NORTHWEST)
                if adj & (me >> (W_plus_1 - 1)):
                    if movement.can_move(Direction.NORTHEAST):
                        options.append(Direction.NORTHEAST)
                if adj & (me << (W_plus_1 - 1)):
                    if movement.can_move(Direction.SOUTHWEST):
                        options.append(Direction.SOUTHWEST)
                if adj & (me << (W_plus_1 + 1)):
                    if movement.can_move(Direction.SOUTHEAST):
                        options.append(Direction.SOUTHEAST)

                if options:
                    movement.move(random.choice(options))
                    return True
                else:
                    print("No path?")
                    return False
        else:
            def move(adj: int) -> bool:
                options: list[Direction] = []
                if adj & (me >> (W_plus_1 + 1)):
                    if movement.can_move(Direction.NORTHWEST):
                        options.append(Direction.NORTHWEST)
                if adj & (me >> (W_plus_1 - 1)):
                    if movement.can_move(Direction.NORTHEAST):
                        options.append(Direction.NORTHEAST)
                if adj & (me << (W_plus_1 - 1)):
                    if movement.can_move(Direction.SOUTHWEST):
                        options.append(Direction.SOUTHWEST)
                if adj & (me << (W_plus_1 + 1)):
                    if movement.can_move(Direction.SOUTHEAST):
                        options.append(Direction.SOUTHEAST)

                if options:
                    movement.move(random.choice(options))
                    return True

                if adj & (me >> W_plus_1):
                    if movement.can_move(Direction.NORTH):
                        options.append(Direction.NORTH)
                if adj & (me >> 1):
                    if movement.can_move(Direction.WEST):
                        options.append(Direction.WEST)
                if adj & (me << 1):
                    if movement.can_move(Direction.EAST):
                        options.append(Direction.EAST)
                if adj & (me << W_plus_1):
                    if movement.can_move(Direction.SOUTH):
                        options.append(Direction.SOUTH)

                if options:
                    movement.move(random.choice(options))
                    return True
                else:
                    print("No path?")
                    return False

        pass_ = self.tile_manager["pass"] & not_unit

        if target & not_unit & adj & pass_:
            return move(target & not_unit & adj & pass_)

        if (target & me) and active:
            return True

        seen = target
        for _ in range(100):
            seen |= seen << 1 | seen >> 1
            seen |= seen << W_plus_1 | seen >> W_plus_1
            seen &= pass_

            if seen & adj:
                return move(seen & adj)

        pass_ = pass_ | self.tile_manager["buildable"] & not_unit

        seen = target
        for _ in range(100):
            seen |= seen << 1 | seen >> 1
            seen |= seen << W_plus_1 | seen >> W_plus_1
            seen &= pass_

            if seen & adj:
                return move(seen & adj)

        print("No path!")
        return False
