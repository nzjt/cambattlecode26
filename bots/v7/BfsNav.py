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

    def multimove(self, c: Controller, targets: list[Position] | int, movement: Movement, active: bool = False) -> None:
        W_plus_1: int = C.W + 1
        target: int = targets if isinstance(targets, int) else sum(
            1 << (y * W_plus_1 + x) for x, y in targets
        )
        not_unit: int = ~self.tile_manager["unit"]

        x, y = c.get_position()
        me: int = 1 << (y * W_plus_1 + x)

        if target & me:
            # Already at target
            return

        adj = me | me << 1 | me >> 1
        adj |= adj << W_plus_1 | adj >> W_plus_1

        hx, hy = self.home
        if ((x - hx) ^ (y - hy)) & 1:
            def move(adj: int):
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
                    return

                if adj & (me >> (W_plus_1 + 1)):
                    if movement.can_move(Direction.NORTHWEST):
                        options.append(Direction.NORTHWEST)
                if adj & (me >> W_plus_1 - 1):
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
                else:
                    print("No path?")
        else:
            def move(adj: int):
                options: list[Direction] = []
                if adj & (me >> (W_plus_1 + 1)):
                    if movement.can_move(Direction.NORTHWEST):
                        options.append(Direction.NORTHWEST)
                if adj & (me >> W_plus_1 - 1):
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
                    return

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
                else:
                    print("No path?")

        if target & not_unit & adj:
            move(target & not_unit & adj)
            return

        g: list[list[bool]] = [[p == 2 for p in row] for row in self.tile_manager.pass_grid]
        for row in g:
            row.append(False)
        g.append([False] * len(g[0]))

        CACHE = BfsNav.CACHE
        byte_tuples: list[tuple] = list(batched(chain.from_iterable(g), 8))
        byte_tuples[-1] += (False,) * (8 - len(byte_tuples[-1]))
        pass_ = int.from_bytes((CACHE[byte] for byte in byte_tuples[:-1]), byteorder='little') & not_unit
        seen = target
        for _ in range(100):
            seen |= seen << 1 | seen >> 1
            seen |= seen << W_plus_1 | seen >> W_plus_1
            seen &= pass_

            if seen & adj:
                move(seen & adj)
                return

        g: list[list[bool]] = [[True if p else False for p in row] for row in self.tile_manager.pass_grid]
        for row in g:
            row.append(False)
        g.append([False] * len(g[0]))

        byte_tuples: list[tuple] = list(batched(chain.from_iterable(g), 8))
        byte_tuples[-1] += (False,) * (8 - len(byte_tuples[-1]))
        pass_ = int.from_bytes((CACHE[byte] for byte in byte_tuples[:-1]), byteorder='little') & not_unit

        seen = target
        for _ in range(100):
            seen |= seen << 1 | seen >> 1
            seen |= seen << W_plus_1 | seen >> W_plus_1
            seen &= pass_

            if seen & adj:
                move(seen & adj)
                return
        print("No path!")

    CACHE = {
        (False, False, False, False, False, False, False, False): 0,
        (False, False, False, False, False, False, False, True): 128,
        (False, False, False, False, False, False, True, False): 64,
        (False, False, False, False, False, False, True, True): 192,
        (False, False, False, False, False, True, False, False): 32,
        (False, False, False, False, False, True, False, True): 160,
        (False, False, False, False, False, True, True, False): 96,
        (False, False, False, False, False, True, True, True): 224,
        (False, False, False, False, True, False, False, False): 16,
        (False, False, False, False, True, False, False, True): 144,
        (False, False, False, False, True, False, True, False): 80,
        (False, False, False, False, True, False, True, True): 208,
        (False, False, False, False, True, True, False, False): 48,
        (False, False, False, False, True, True, False, True): 176,
        (False, False, False, False, True, True, True, False): 112,
        (False, False, False, False, True, True, True, True): 240,
        (False, False, False, True, False, False, False, False): 8,
        (False, False, False, True, False, False, False, True): 136,
        (False, False, False, True, False, False, True, False): 72,
        (False, False, False, True, False, False, True, True): 200,
        (False, False, False, True, False, True, False, False): 40,
        (False, False, False, True, False, True, False, True): 168,
        (False, False, False, True, False, True, True, False): 104,
        (False, False, False, True, False, True, True, True): 232,
        (False, False, False, True, True, False, False, False): 24,
        (False, False, False, True, True, False, False, True): 152,
        (False, False, False, True, True, False, True, False): 88,
        (False, False, False, True, True, False, True, True): 216,
        (False, False, False, True, True, True, False, False): 56,
        (False, False, False, True, True, True, False, True): 184,
        (False, False, False, True, True, True, True, False): 120,
        (False, False, False, True, True, True, True, True): 248,
        (False, False, True, False, False, False, False, False): 4,
        (False, False, True, False, False, False, False, True): 132,
        (False, False, True, False, False, False, True, False): 68,
        (False, False, True, False, False, False, True, True): 196,
        (False, False, True, False, False, True, False, False): 36,
        (False, False, True, False, False, True, False, True): 164,
        (False, False, True, False, False, True, True, False): 100,
        (False, False, True, False, False, True, True, True): 228,
        (False, False, True, False, True, False, False, False): 20,
        (False, False, True, False, True, False, False, True): 148,
        (False, False, True, False, True, False, True, False): 84,
        (False, False, True, False, True, False, True, True): 212,
        (False, False, True, False, True, True, False, False): 52,
        (False, False, True, False, True, True, False, True): 180,
        (False, False, True, False, True, True, True, False): 116,
        (False, False, True, False, True, True, True, True): 244,
        (False, False, True, True, False, False, False, False): 12,
        (False, False, True, True, False, False, False, True): 140,
        (False, False, True, True, False, False, True, False): 76,
        (False, False, True, True, False, False, True, True): 204,
        (False, False, True, True, False, True, False, False): 44,
        (False, False, True, True, False, True, False, True): 172,
        (False, False, True, True, False, True, True, False): 108,
        (False, False, True, True, False, True, True, True): 236,
        (False, False, True, True, True, False, False, False): 28,
        (False, False, True, True, True, False, False, True): 156,
        (False, False, True, True, True, False, True, False): 92,
        (False, False, True, True, True, False, True, True): 220,
        (False, False, True, True, True, True, False, False): 60,
        (False, False, True, True, True, True, False, True): 188,
        (False, False, True, True, True, True, True, False): 124,
        (False, False, True, True, True, True, True, True): 252,
        (False, True, False, False, False, False, False, False): 2,
        (False, True, False, False, False, False, False, True): 130,
        (False, True, False, False, False, False, True, False): 66,
        (False, True, False, False, False, False, True, True): 194,
        (False, True, False, False, False, True, False, False): 34,
        (False, True, False, False, False, True, False, True): 162,
        (False, True, False, False, False, True, True, False): 98,
        (False, True, False, False, False, True, True, True): 226,
        (False, True, False, False, True, False, False, False): 18,
        (False, True, False, False, True, False, False, True): 146,
        (False, True, False, False, True, False, True, False): 82,
        (False, True, False, False, True, False, True, True): 210,
        (False, True, False, False, True, True, False, False): 50,
        (False, True, False, False, True, True, False, True): 178,
        (False, True, False, False, True, True, True, False): 114,
        (False, True, False, False, True, True, True, True): 242,
        (False, True, False, True, False, False, False, False): 10,
        (False, True, False, True, False, False, False, True): 138,
        (False, True, False, True, False, False, True, False): 74,
        (False, True, False, True, False, False, True, True): 202,
        (False, True, False, True, False, True, False, False): 42,
        (False, True, False, True, False, True, False, True): 170,
        (False, True, False, True, False, True, True, False): 106,
        (False, True, False, True, False, True, True, True): 234,
        (False, True, False, True, True, False, False, False): 26,
        (False, True, False, True, True, False, False, True): 154,
        (False, True, False, True, True, False, True, False): 90,
        (False, True, False, True, True, False, True, True): 218,
        (False, True, False, True, True, True, False, False): 58,
        (False, True, False, True, True, True, False, True): 186,
        (False, True, False, True, True, True, True, False): 122,
        (False, True, False, True, True, True, True, True): 250,
        (False, True, True, False, False, False, False, False): 6,
        (False, True, True, False, False, False, False, True): 134,
        (False, True, True, False, False, False, True, False): 70,
        (False, True, True, False, False, False, True, True): 198,
        (False, True, True, False, False, True, False, False): 38,
        (False, True, True, False, False, True, False, True): 166,
        (False, True, True, False, False, True, True, False): 102,
        (False, True, True, False, False, True, True, True): 230,
        (False, True, True, False, True, False, False, False): 22,
        (False, True, True, False, True, False, False, True): 150,
        (False, True, True, False, True, False, True, False): 86,
        (False, True, True, False, True, False, True, True): 214,
        (False, True, True, False, True, True, False, False): 54,
        (False, True, True, False, True, True, False, True): 182,
        (False, True, True, False, True, True, True, False): 118,
        (False, True, True, False, True, True, True, True): 246,
        (False, True, True, True, False, False, False, False): 14,
        (False, True, True, True, False, False, False, True): 142,
        (False, True, True, True, False, False, True, False): 78,
        (False, True, True, True, False, False, True, True): 206,
        (False, True, True, True, False, True, False, False): 46,
        (False, True, True, True, False, True, False, True): 174,
        (False, True, True, True, False, True, True, False): 110,
        (False, True, True, True, False, True, True, True): 238,
        (False, True, True, True, True, False, False, False): 30,
        (False, True, True, True, True, False, False, True): 158,
        (False, True, True, True, True, False, True, False): 94,
        (False, True, True, True, True, False, True, True): 222,
        (False, True, True, True, True, True, False, False): 62,
        (False, True, True, True, True, True, False, True): 190,
        (False, True, True, True, True, True, True, False): 126,
        (False, True, True, True, True, True, True, True): 254,
        (True, False, False, False, False, False, False, False): 1,
        (True, False, False, False, False, False, False, True): 129,
        (True, False, False, False, False, False, True, False): 65,
        (True, False, False, False, False, False, True, True): 193,
        (True, False, False, False, False, True, False, False): 33,
        (True, False, False, False, False, True, False, True): 161,
        (True, False, False, False, False, True, True, False): 97,
        (True, False, False, False, False, True, True, True): 225,
        (True, False, False, False, True, False, False, False): 17,
        (True, False, False, False, True, False, False, True): 145,
        (True, False, False, False, True, False, True, False): 81,
        (True, False, False, False, True, False, True, True): 209,
        (True, False, False, False, True, True, False, False): 49,
        (True, False, False, False, True, True, False, True): 177,
        (True, False, False, False, True, True, True, False): 113,
        (True, False, False, False, True, True, True, True): 241,
        (True, False, False, True, False, False, False, False): 9,
        (True, False, False, True, False, False, False, True): 137,
        (True, False, False, True, False, False, True, False): 73,
        (True, False, False, True, False, False, True, True): 201,
        (True, False, False, True, False, True, False, False): 41,
        (True, False, False, True, False, True, False, True): 169,
        (True, False, False, True, False, True, True, False): 105,
        (True, False, False, True, False, True, True, True): 233,
        (True, False, False, True, True, False, False, False): 25,
        (True, False, False, True, True, False, False, True): 153,
        (True, False, False, True, True, False, True, False): 89,
        (True, False, False, True, True, False, True, True): 217,
        (True, False, False, True, True, True, False, False): 57,
        (True, False, False, True, True, True, False, True): 185,
        (True, False, False, True, True, True, True, False): 121,
        (True, False, False, True, True, True, True, True): 249,
        (True, False, True, False, False, False, False, False): 5,
        (True, False, True, False, False, False, False, True): 133,
        (True, False, True, False, False, False, True, False): 69,
        (True, False, True, False, False, False, True, True): 197,
        (True, False, True, False, False, True, False, False): 37,
        (True, False, True, False, False, True, False, True): 165,
        (True, False, True, False, False, True, True, False): 101,
        (True, False, True, False, False, True, True, True): 229,
        (True, False, True, False, True, False, False, False): 21,
        (True, False, True, False, True, False, False, True): 149,
        (True, False, True, False, True, False, True, False): 85,
        (True, False, True, False, True, False, True, True): 213,
        (True, False, True, False, True, True, False, False): 53,
        (True, False, True, False, True, True, False, True): 181,
        (True, False, True, False, True, True, True, False): 117,
        (True, False, True, False, True, True, True, True): 245,
        (True, False, True, True, False, False, False, False): 13,
        (True, False, True, True, False, False, False, True): 141,
        (True, False, True, True, False, False, True, False): 77,
        (True, False, True, True, False, False, True, True): 205,
        (True, False, True, True, False, True, False, False): 45,
        (True, False, True, True, False, True, False, True): 173,
        (True, False, True, True, False, True, True, False): 109,
        (True, False, True, True, False, True, True, True): 237,
        (True, False, True, True, True, False, False, False): 29,
        (True, False, True, True, True, False, False, True): 157,
        (True, False, True, True, True, False, True, False): 93,
        (True, False, True, True, True, False, True, True): 221,
        (True, False, True, True, True, True, False, False): 61,
        (True, False, True, True, True, True, False, True): 189,
        (True, False, True, True, True, True, True, False): 125,
        (True, False, True, True, True, True, True, True): 253,
        (True, True, False, False, False, False, False, False): 3,
        (True, True, False, False, False, False, False, True): 131,
        (True, True, False, False, False, False, True, False): 67,
        (True, True, False, False, False, False, True, True): 195,
        (True, True, False, False, False, True, False, False): 35,
        (True, True, False, False, False, True, False, True): 163,
        (True, True, False, False, False, True, True, False): 99,
        (True, True, False, False, False, True, True, True): 227,
        (True, True, False, False, True, False, False, False): 19,
        (True, True, False, False, True, False, False, True): 147,
        (True, True, False, False, True, False, True, False): 83,
        (True, True, False, False, True, False, True, True): 211,
        (True, True, False, False, True, True, False, False): 51,
        (True, True, False, False, True, True, False, True): 179,
        (True, True, False, False, True, True, True, False): 115,
        (True, True, False, False, True, True, True, True): 243,
        (True, True, False, True, False, False, False, False): 11,
        (True, True, False, True, False, False, False, True): 139,
        (True, True, False, True, False, False, True, False): 75,
        (True, True, False, True, False, False, True, True): 203,
        (True, True, False, True, False, True, False, False): 43,
        (True, True, False, True, False, True, False, True): 171,
        (True, True, False, True, False, True, True, False): 107,
        (True, True, False, True, False, True, True, True): 235,
        (True, True, False, True, True, False, False, False): 27,
        (True, True, False, True, True, False, False, True): 155,
        (True, True, False, True, True, False, True, False): 91,
        (True, True, False, True, True, False, True, True): 219,
        (True, True, False, True, True, True, False, False): 59,
        (True, True, False, True, True, True, False, True): 187,
        (True, True, False, True, True, True, True, False): 123,
        (True, True, False, True, True, True, True, True): 251,
        (True, True, True, False, False, False, False, False): 7,
        (True, True, True, False, False, False, False, True): 135,
        (True, True, True, False, False, False, True, False): 71,
        (True, True, True, False, False, False, True, True): 199,
        (True, True, True, False, False, True, False, False): 39,
        (True, True, True, False, False, True, False, True): 167,
        (True, True, True, False, False, True, True, False): 103,
        (True, True, True, False, False, True, True, True): 231,
        (True, True, True, False, True, False, False, False): 23,
        (True, True, True, False, True, False, False, True): 151,
        (True, True, True, False, True, False, True, False): 87,
        (True, True, True, False, True, False, True, True): 215,
        (True, True, True, False, True, True, False, False): 55,
        (True, True, True, False, True, True, False, True): 183,
        (True, True, True, False, True, True, True, False): 119,
        (True, True, True, False, True, True, True, True): 247,
        (True, True, True, True, False, False, False, False): 15,
        (True, True, True, True, False, False, False, True): 143,
        (True, True, True, True, False, False, True, False): 79,
        (True, True, True, True, False, False, True, True): 207,
        (True, True, True, True, False, True, False, False): 47,
        (True, True, True, True, False, True, False, True): 175,
        (True, True, True, True, False, True, True, False): 111,
        (True, True, True, True, False, True, True, True): 239,
        (True, True, True, True, True, False, False, False): 31,
        (True, True, True, True, True, False, False, True): 159,
        (True, True, True, True, True, False, True, False): 95,
        (True, True, True, True, True, False, True, True): 223,
        (True, True, True, True, True, True, False, False): 63,
        (True, True, True, True, True, True, False, True): 191,
        (True, True, True, True, True, True, True, False): 127,
        (True, True, True, True, True, True, True, True): 255
    }

