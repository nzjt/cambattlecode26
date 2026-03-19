from cambc import *
from TileManager import TileManager
import random


class Bfs:
    ADJ = 0xe0380e00000000

    def __init__(self, tile_manager: TileManager):
        self.tile_manager = tile_manager
        self.conveyor_reach: int = 0

    def update(self):
        pass_ = self.tile_manager.buildable
        conveyor_reach = 0x100000000000

        for _ in range(15):
            conveyor_reach |= conveyor_reach << 1 | conveyor_reach >> 1 | conveyor_reach << 10 | conveyor_reach >> 10
            conveyor_reach &= pass_

        conveyor_reach |= conveyor_reach << 1 | conveyor_reach >> 1 | conveyor_reach << 10 | conveyor_reach >> 10
        self.conveyor_reach = conveyor_reach

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

    def bfs_adj_exc(self, dx: int, dy: int, pass_: int) -> Direction | None:
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
