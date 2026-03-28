from cambc import *
from TileManager import TileManager
import random


class Bfs:
    ADJ = 0xe0380e00000000

    def __init__(self, home: Position, tile_manager: TileManager):
        self.home: Position = home
        self.tile_manager = tile_manager
        self.reach: int = 0
        self.get_move = None

    def update(self, c: Controller, conveyor_manager):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)

        pass_ = (self.tile_manager.pass_ | self.tile_manager.buildable) & ~self.tile_manager.ally & ~self.tile_manager.enemy
        reach: int = 1 << 44
        for _ in range(15):
            reach |= reach << 1 | reach >> 1
            reach |= reach << 10 | reach >> 10
            reach &= pass_

        self.reach = reach
        
        dx = my_pos.x - self.home.x
        dy = my_pos.y - self.home.y
        self.get_move = self.get_move_cardinal if (dx ^ dy) & 1 else self.get_move_diagonal

    def can_reach(self, dx: int, dy: int) -> int:
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            return self.reach >> (dx + dy * 10 + 44) & 1
        return 0

    def can_reach_adj(self, dx: int, dy: int) -> int:
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            target: int = 1 << (dx + dy * 10 + 44)
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            return self.reach & target
        return 0

    def bfs(self, target: int, pass_: int) -> Direction | None:
        if target >> 44 & 1:
            return Direction.CENTRE

        ADJ = Bfs.ADJ
        if target & ADJ:
            return self.get_move(target & ADJ)

        for _ in range(15):
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            target &= pass_

            if target & ADJ:
                return self.get_move(target & ADJ)

    def bfs_along_path(self, path: list[tuple[int, int]], pass_: int) -> Direction | None:
        target: int = 0
        ADJ = Bfs.ADJ

        for dx, dy in reversed(path):
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10

            if -4 <= dx <= 4 and -4 <= dy <= 4:
                target |= 1 << (dx + dy * 10 + 44)

            target &= pass_

            if target & ADJ:
                return self.get_move(target & ADJ)

        for _ in range(5):
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            target &= pass_

            if target & ADJ:
                return self.get_move(target & ADJ)

    def bfs_to_pos(self, dx: int, dy: int, pass_: int):
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            target = 1 << (dx + dy * 10 + 44)

            if target >> 44 & 1:
                return Direction.CENTRE

            ADJ = Bfs.ADJ
            if target & ADJ:
                return self.get_move(target & ADJ)

            for _ in range(15):
                target |= target << 1 | target >> 1
                target |= target << 10 | target >> 10
                target &= pass_

                if target & ADJ:
                    return self.get_move(target & ADJ)

    def bfs_adj_exc(self, dx: int, dy: int, pass_: int, active: bool = False) -> Direction | None:
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            centre = 1 << (dx + dy * 10 + 44)
            target = centre
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            target &= pass_ & ~centre

            if active:
                ADJ = Bfs.ADJ & ~(1 << 44)
                if target & ADJ:
                    return self.get_move(target & ADJ)

                for _ in range(15):
                    target |= target << 1 | target >> 1
                    target |= target << 10 | target >> 10
                    target &= pass_

                    if target & ADJ:
                        return self.get_move(target & ADJ)

                if target >> 44 & 1:
                    return Direction.CENTRE
            else:
                if target >> 44 & 1:
                    return Direction.CENTRE

                ADJ = Bfs.ADJ
                if target & ADJ:
                    return self.get_move(target & ADJ)

                for _ in range(15):
                    target |= target << 1 | target >> 1
                    target |= target << 10 | target >> 10
                    target &= pass_

                    if target & ADJ:
                        return self.get_move(target & ADJ)

    def bfs_adj(self, dx: int, dy: int, pass_: int) -> Direction | None:
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            target = 1 << (dx + dy * 10 + 44)
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            target &= pass_

            if target >> 44 & 1:
                return Direction.CENTRE

            ADJ = Bfs.ADJ
            if target & ADJ:
                return self.get_move(target & ADJ)

            for _ in range(15):
                target |= target << 1 | target >> 1
                target |= target << 10 | target >> 10
                target &= pass_

                if target & ADJ:
                    return self.get_move(target & ADJ)

    def bfs_adj_exc_multi(self, targets: list[tuple[int, int]], pass_: int) -> Direction | None:
        target: int = 0
        for dx, dy in targets:
            if -4 <= dx <= 4 and -4 <= dy <= 4:
                centre = 1 << (dx + dy * 10 + 44)
                adj = centre
                adj |= adj << 1 | adj >> 1
                adj |= adj << 10 | adj >> 10
                target |= adj & pass_ & ~centre

        if target >> 44 & 1:
            return Direction.CENTRE

        ADJ = Bfs.ADJ
        if target & ADJ:
            return self.get_move(target & ADJ)

        for _ in range(15):
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            target &= pass_

            if target & ADJ:
                return self.get_move(target & ADJ)

    @staticmethod
    def closest_start(start: int, end: int, pass_: int) -> list[tuple[int, int]]:
        if start & end:
            i = (start & end).bit_length() - 1
            return [(i % 10 - 4, i // 10 - 4)]

        dp: list[int] = [0] * 16
        dp[0] = end

        for i in range(1, len(dp)):
            prev = dp[i - 2]
            prev |= prev << 1 | prev >> 1
            prev |= prev << 10 | prev >> 10
            end |= end << 1 | end >> 1 | end << 10 | end >> 10 | prev
            end &= pass_
            dp[i] = end

            intersection = start & end
            if intersection:
                j = intersection.bit_length() - 1
                path: list[tuple[int, int]] = []
                while True:
                    path.append((j % 10 - 4, j // 10 - 4))
                    if not i:
                        break
                    end = dp[i - 1]
                    if j >= 1 and end >> (j - 1) & 1:
                        j -= 1
                    elif end >> (j + 1) & 1:
                        j += 1
                    elif j >= 10 and end >> (j - 10) & 1:
                        j -= 10
                    elif end >> (j + 10) & 1:
                        j += 10
                    else:
                        end = dp[i - 2]
                        if j >= 11 and end >> (j - 11) & 1:
                            j -= 11
                        elif j >= 9 and end >> (j - 9) & 1:
                            j -= 9
                        elif end >> (j + 9) & 1:
                            j += 9
                        elif end >> (j + 11) & 1:
                            j += 11
                        i -= 1
                    i -= 1
                return path

        return []

    @staticmethod
    def get_move_cardinal(adj: int) -> Direction:
        options = []

        if adj >> 34 & 1:
            options.append(Direction.NORTH)
        if adj >> 43 & 1:
            options.append(Direction.WEST)
        if adj >> 45 & 1:
            options.append(Direction.EAST)
        if adj >> 54 & 1:
            options.append(Direction.SOUTH)

        if options:
            return random.choice(options)

        if adj >> 33 & 1:
            options.append(Direction.NORTHWEST)
        if adj >> 35 & 1:
            options.append(Direction.NORTHEAST)
        if adj >> 53 & 1:
            options.append(Direction.SOUTHWEST)
        if adj >> 55 & 1:
            options.append(Direction.SOUTHEAST)

        if options:
            return random.choice(options)
        else:
            return Direction.CENTRE

    @staticmethod
    def get_move_diagonal(adj: int) -> Direction:
        options = []

        if adj >> 33 & 1:
            options.append(Direction.NORTHWEST)
        if adj >> 35 & 1:
            options.append(Direction.NORTHEAST)
        if adj >> 53 & 1:
            options.append(Direction.SOUTHWEST)
        if adj >> 55 & 1:
            options.append(Direction.SOUTHEAST)

        if options:
            return random.choice(options)

        if adj >> 34 & 1:
            options.append(Direction.NORTH)
        if adj >> 43 & 1:
            options.append(Direction.WEST)
        if adj >> 45 & 1:
            options.append(Direction.EAST)
        if adj >> 54 & 1:
            options.append(Direction.SOUTH)

        if options:
            return random.choice(options)
        else:
            return Direction.CENTRE
