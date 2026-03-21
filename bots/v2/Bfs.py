from cambc import *
from TileManager import TileManager
import random


class Bfs:
    ADJ = 0xe0380e00000000

    def __init__(self, tile_manager: TileManager):
        self.tile_manager = tile_manager
        self.conveyor_reach: int = 0

    def update(self, c: Controller, conveyor_manager):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)

        if conveyor_manager is not None:
            pass_ = self.tile_manager.buildable
            xi, yi = conveyor_manager.path[-1]
            dx = xi - my_pos.x
            dy = yi - my_pos.y
            if -4 <= dx <= 4 and -4 <= dy <= 4:
                conveyor_reach = 1 << (dx + dy * 10 + 44)
                for _ in range(15):
                    conveyor_reach |= conveyor_reach << 1 | conveyor_reach >> 1 | conveyor_reach << 10 | conveyor_reach >> 10
                    conveyor_reach &= pass_

                conveyor_reach |= conveyor_reach << 1 | conveyor_reach >> 1 | conveyor_reach << 10 | conveyor_reach >> 10
                self.conveyor_reach = conveyor_reach
            else:
                self.conveyor_reach = 0

    def can_conveyor_reach(self, dx: int, dy: int) -> int:
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            return self.conveyor_reach >> (dx + dy * 10 + 44) & 1
        return False

    def bfs(self, target: int, pass_: int) -> Direction | None:
        if target >> 44 & 1:
            return Direction.CENTRE

        ADJ = Bfs.ADJ
        if target & ADJ:
            return Bfs.get_move(target & ADJ)

        for _ in range(15):
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            target &= pass_

            if target & ADJ:
                return Bfs.get_move(target & ADJ)

    @staticmethod
    def bfs_to_pos(dx: int, dy: int, pass_: int):
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            target = 1 << (dx + dy * 10 + 44)

            if target >> 44 & 1:
                return Direction.CENTRE

            ADJ = Bfs.ADJ
            if target & ADJ:
                return Bfs.get_move(target & ADJ)

            for _ in range(15):
                target |= target << 1 | target >> 1
                target |= target << 10 | target >> 10
                target &= pass_

                if target & ADJ:
                    return Bfs.get_move(target & ADJ)

    @staticmethod
    def bfs_adj_exc(dx: int, dy: int, pass_: int) -> Direction | None:
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            centre = 1 << (dx + dy * 10 + 44)
            target = centre
            target |= target << 1 | target >> 1
            target |= target << 10 | target >> 10
            target &= pass_ & ~centre

            if target >> 44 & 1:
                return Direction.CENTRE

            ADJ = Bfs.ADJ
            if target & ADJ:
                return Bfs.get_move(target & ADJ)

            for _ in range(15):
                target |= target << 1 | target >> 1
                target |= target << 10 | target >> 10
                target &= pass_

                if target & ADJ:
                    return Bfs.get_move(target & ADJ)

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
    def get_move(adj: int) -> Direction:
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

        return random.choice(options)
