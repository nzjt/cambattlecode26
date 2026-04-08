import time

from cambc import *
from TileManager import TileManager
import consts as C


class AStarJPSOptimised:
    INF = 1000000

    def __init__(self, tile_manager: TileManager, mode: int = 0):
        self.tile_manager = tile_manager
        INF = AStarJPSOptimised.INF
        if mode == 0:
            # Conveyor nav (avoid joining)
            self.g: list[list[int]] = [[INF if e == 2 else -1 for e in row] for row in self.tile_manager.env_grid]
        elif mode == 1:
            # Conveyor nav (avoid joining)
            self.g: list[list[int]] = [[INF if 2 <= e <= 3 else -1 for e in row] for row in self.tile_manager.env_grid]
        elif mode == 2:
            # Bot nav (rich)
            self.g: list[list[int]] = [[INF if p else -1 for p in row] for row in self.tile_manager.pass_grid]
        else:
            # Bot nav (rich)
            self.g: list[list[int]] = [[INF if p == 2 else -1 for p in row] for row in self.tile_manager.pass_grid]

        for row in self.g:
            row.append(-1)
        self.g.append([-1] * len(self.g[0]))
        self.par: list[list[tuple[int, int] | None]] = [[None] * len(self.g[0]) for _ in range(len(self.g))]
        self.path: list[Position] = []

    def compute(self, start: Position, end: list[Position], is_core: bool = False):
        g: list[list[int]] = self.g
        x, y = start
        g[y][x] = AStarJPSOptimised.INF
        W_plus_1, H_plus_1 = C.W + 1, C.H + 1
        target_bit = 1 << (y * W_plus_1 + x)

        bitset = int(''.join(''.join('1' if tile != -1 else '0' for tile in row) for row in g)[::-1], 2)
        bitset_minus_1: int = bitset >> W_plus_1
        bitset_plus_1: int = bitset << W_plus_1

        is_jump_E: int = ((~bitset_minus_1 & bitset_minus_1 >> 1) | (~bitset_plus_1 & bitset_plus_1 >> 1)) & bitset
        is_jump_E |= target_bit

        lookahead_E = is_jump_E | is_jump_E >> 1 & bitset
        bitmask = bitset & bitset >> 1
        lookahead_E |= lookahead_E >> 2 & bitmask
        bitmask &= bitmask >> 2
        lookahead_E |= lookahead_E >> 4 & bitmask
        bitmask &= bitmask >> 4
        lookahead_E |= lookahead_E >> 8 & bitmask
        bitmask &= bitmask >> 8
        lookahead_E |= lookahead_E >> 16 & bitmask
        bitmask &= bitmask >> 16
        lookahead_E |= lookahead_E >> 32 & bitmask

        lookahead_E >>= 1

        is_jump_W: int = ((~bitset_minus_1 & bitset_minus_1 << 1) | (~bitset_plus_1 & bitset_plus_1 << 1)) & bitset
        is_jump_W |= target_bit

        lookahead_W = is_jump_W | is_jump_W << 1 & bitset
        bitmask = bitset & bitset << 1
        lookahead_W |= lookahead_W << 2 & bitmask
        bitmask &= bitmask << 2
        lookahead_W |= lookahead_W << 4 & bitmask
        bitmask &= bitmask << 4
        lookahead_W |= lookahead_W << 8 & bitmask
        bitmask &= bitmask << 8
        lookahead_W |= lookahead_W << 16 & bitmask
        bitmask &= bitmask << 16
        lookahead_W |= lookahead_W << 32 & bitmask

        lookahead_W <<= 1

        bitset_minus_1: int = bitset >> 1
        bitset_plus_1: int = bitset << 1

        is_jump_S: int = ((~bitset_minus_1 & bitset_minus_1 >> W_plus_1) | (~bitset_plus_1 & bitset_plus_1 >> W_plus_1)) & bitset
        is_jump_S |= target_bit

        lookahead_S = is_jump_S | is_jump_S >> W_plus_1 & bitset
        bitmask = bitset & bitset >> W_plus_1
        shift: int = W_plus_1 << 1
        lookahead_S |= lookahead_S >> shift & bitmask
        bitmask &= bitmask >> shift
        shift <<= 1
        lookahead_S |= lookahead_S >> shift & bitmask
        bitmask &= bitmask >> shift
        shift <<= 1
        lookahead_S |= lookahead_S >> shift & bitmask
        bitmask &= bitmask >> shift
        shift <<= 1
        lookahead_S |= lookahead_S >> shift & bitmask
        bitmask &= bitmask >> shift
        lookahead_S |= lookahead_S >> (shift << 1) & bitmask

        lookahead_S >>= W_plus_1

        is_jump_N: int = ((~bitset_minus_1 & bitset_minus_1 << W_plus_1) | (~bitset_plus_1 & bitset_plus_1 << W_plus_1)) & bitset
        is_jump_N |= target_bit

        lookahead_N = is_jump_N | is_jump_N << W_plus_1 & bitset
        bitmask = bitset & bitset << W_plus_1
        shift: int = W_plus_1 << 1
        lookahead_N |= lookahead_N << shift & bitmask
        bitmask &= bitmask << shift
        shift <<= 1
        lookahead_N |= lookahead_N << shift & bitmask
        bitmask &= bitmask << shift
        shift <<= 1
        lookahead_N |= lookahead_N << shift & bitmask
        bitmask &= bitmask << shift
        shift <<= 1
        lookahead_N |= lookahead_N << shift & bitmask
        bitmask &= bitmask << shift
        lookahead_N |= lookahead_N << (shift << 1) & bitmask

        lookahead_N <<= W_plus_1

        lookahead_NE = target_bit | lookahead_N | lookahead_E | bitset << (W_plus_1 + 1) & ~bitset << 1 | bitset >> (W_plus_1 + 1) & ~bitset >> W_plus_1
        lookahead_SE = target_bit | lookahead_S | lookahead_E | bitset << (W_plus_1 - 1) & ~bitset << W_plus_1 | bitset >> (W_plus_1 - 1) & ~bitset << 1
        lookahead_SW = target_bit | lookahead_S | lookahead_W | bitset >> (W_plus_1 + 1) & ~bitset >> 1 | bitset << (W_plus_1 + 1) & ~bitset << W_plus_1
        lookahead_NW = target_bit | lookahead_N | lookahead_W | bitset >> (W_plus_1 - 1) & ~bitset >> W_plus_1 | bitset << (W_plus_1 - 1) & ~bitset >> 1

        par = self.par

        queue: list[list[tuple[int, int, int]]] = [[] for _ in range(200)]

        def add_source(xj: int, yj: int, d: int):
            g[yj][xj] = 0
            queue[max(abs(xj - x), abs(yj - y))].append((xj, yj, d))

        def add(xj: int, yj: int, gi: int, d: int):
            if gi < g[yj][xj]:
                g[yj][xj] = gi
                queue[g[yj][xj] + max(abs(xj - x), abs(yj - y))].append((xj, yj, d))
                par[yj][xj] = (xi, yi)

        def scan_N(xj, yj) -> tuple[int, int] | None:
            index = yj * W_plus_1 + xj
            while True:
                yj -= 1
                if g[yj][xj] == -1:
                    return
                index -= W_plus_1
                if is_jump_N >> index & 1:
                    return xj, yj

        def scan_E(xj, yj) -> tuple[int, int] | None:
            while True:
                xj += 1
                if g[yj][xj] == -1:
                    return
                if is_jump_E >> (yj * W_plus_1 + xj) & 1:
                    return xj, yj

        def scan_S(xj, yj) -> tuple[int, int] | None:
            while True:
                yj += 1
                if g[yj][xj] == -1:
                    return
                if is_jump_S >> (yj * W_plus_1 + xj) & 1:
                    return xj, yj

        def scan_W(xj, yj) -> tuple[int, int] | None:
            while True:
                xj -= 1
                if g[yj][xj] == -1:
                    return
                if is_jump_W >> (yj * W_plus_1 + xj) & 1:
                    return xj, yj

        def scan_NE(xj, yj) -> tuple[int, int] | None:
            while True:
                xj += 1
                yj -= 1
                if g[yj][xj] == -1:
                    return
                if lookahead_NE >> (yj * W_plus_1 + xj) & 1:
                    return xj, yj

        def scan_SE(xj, yj) -> tuple[int, int] | None:
            while True:
                xj += 1
                yj += 1
                if g[yj][xj] == -1:
                    return
                if lookahead_SE >> (yj * W_plus_1 + xj) & 1:
                    return xj, yj

        def scan_SW(xj, yj) -> tuple[int, int] | None:
            while True:
                xj -= 1
                yj += 1
                if g[yj][xj] == -1:
                    return
                if lookahead_SW >> (yj * W_plus_1 + xj) & 1:
                    return xj, yj

        def scan_NW(xj, yj) -> tuple[int, int] | None:
            while True:
                xj -= 1
                yj -= 1
                if g[yj][xj] == -1:
                    return
                if lookahead_NW >> (yj * W_plus_1 + xj) & 1:
                    return xj, yj

        if is_core:
            xi, yi = end[0]
            add_source(xi, yi - 1, 0)
            add_source(xi + 1, yi - 1, 1)
            add_source(xi + 1, yi, 2)
            add_source(xi + 1, yi + 1, 3)
            add_source(xi, yi + 1, 4)
            add_source(xi - 1, yi + 1, 5)
            add_source(xi - 1, yi, 6)
            add_source(xi - 1, yi - 1, 7)
        else:
            for xi, yi in end:
                g[yi][xi] = 0
                queue[max(abs(xi - x), abs(yi - y))].append((xi, yi, 8))

        def expand_N(xi, yi):
            gi = g[yi][xi]

            jp = scan_N(xi, yi)
            if jp:
                add(*jp, gi + yi - jp[1], 0)
            if g[yi][xi - 1] == -1 and g[yi - 1][xi - 1] != -1:
                jp = scan_NW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 7)
            if g[yi][xi + 1] == -1 and g[yi - 1][xi + 1] != -1:
                jp = scan_NE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 1)

        def expand_NE(xi, yi):
            gi = g[yi][xi]

            jp = scan_N(xi, yi)
            if jp:
                add(*jp, gi + yi - jp[1], 0)
            jp = scan_NE(xi, yi)
            if jp:
                add(*jp, gi + jp[0] - xi, 1)
            jp = scan_E(xi, yi)
            if jp:
                add(*jp, gi + jp[0] - xi, 2)
            if g[yi][xi - 1] == -1 and g[yi - 1][xi - 1] != -1:
                jp = scan_NW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 7)
            if g[yi + 1][xi] == -1 and g[yi + 1][xi + 1] != -1:
                jp = scan_SE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 3)

        def expand_E(xi, yi):
            gi = g[yi][xi]

            jp = scan_E(xi, yi)
            if jp:
                add(*jp, gi + jp[0] - xi, 2)
            if g[yi - 1][xi] == -1 and g[yi - 1][xi + 1] != -1:
                jp = scan_NE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 1)
            if g[yi + 1][xi] == -1 and g[yi + 1][xi + 1] != -1:
                jp = scan_SE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 3)

        def expand_SE(xi, yi):
            gi = g[yi][xi]

            jp = scan_E(xi, yi)
            if jp:
                add(*jp, gi + jp[0] - xi, 2)
            jp = scan_SE(xi, yi)
            if jp:
                add(*jp, gi + jp[0] - xi, 3)
            jp = scan_S(xi, yi)
            if jp:
                add(*jp, gi + jp[1] - yi, 4)
            if g[yi - 1][xi] == -1 and g[yi - 1][xi + 1] != -1:
                jp = scan_NE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 1)
            if g[yi][xi - 1] == -1 and g[yi + 1][xi - 1] != -1:
                jp = scan_SW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 5)

        def expand_S(xi, yi):
            gi = g[yi][xi]

            jp = scan_S(xi, yi)
            if jp:
                add(*jp, gi + jp[1] - yi, 4)
            if g[yi][xi + 1] == -1 and g[yi + 1][xi + 1] != -1:
                jp = scan_SE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 3)
            if g[yi][xi - 1] == -1 and g[yi + 1][xi - 1] != -1:
                jp = scan_SW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 5)

        def expand_SW(xi, yi):
            gi = g[yi][xi]

            jp = scan_S(xi, yi)
            if jp:
                add(*jp, gi + jp[1] - yi, 4)
            jp = scan_SW(xi, yi)
            if jp:
                add(*jp, gi + xi - jp[0], 5)
            jp = scan_W(xi, yi)
            if jp:
                add(*jp, gi + xi - jp[0], 6)
            if g[yi][xi + 1] == -1 and g[yi + 1][xi + 1] != -1:
                jp = scan_SE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 3)
            if g[yi - 1][xi] == -1 and g[yi - 1][xi - 1] != -1:
                jp = scan_NW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 7)

        def expand_W(xi, yi):
            gi = g[yi][xi]

            jp = scan_W(xi, yi)
            if jp:
                add(*jp, gi + xi - jp[0], 6)
            jp = scan_NW(xi, yi)
            if jp:
                add(*jp, gi + xi - jp[0], 7)
            if g[yi + 1][xi] == -1 and g[yi + 1][xi - 1] != -1:
                jp = scan_SW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 5)
            if g[yi - 1][xi] == -1 and g[yi - 1][xi - 1] != -1:
                jp = scan_NW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 7)

        def expand_NW(xi, yi):
            gi = g[yi][xi]

            jp = scan_W(xi, yi)
            if jp:
                add(*jp, gi + xi - jp[0], 6)
            jp = scan_NW(xi, yi)
            if jp:
                add(*jp, gi + xi - jp[0], 7)
            jp = scan_N(xi, yi)
            if jp:
                add(*jp, gi + yi - jp[1], 0)
            if g[yi + 1][xi] == -1 and g[yi + 1][xi - 1] != -1:
                jp = scan_SW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 5)
            if g[yi][xi + 1] == -1 and g[yi - 1][xi + 1] != -1:
                jp = scan_NE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 1)

        def expand_all(xi, yi):
            jp = scan_N(xi, yi)
            if jp:
                add(*jp, yi - jp[1], 0)
            jp = scan_NE(xi, yi)
            if jp:
                add(*jp, jp[0] - xi, 1)
            jp = scan_E(xi, yi)
            if jp:
                add(*jp, jp[0] - xi, 2)
            jp = scan_SE(xi, yi)
            if jp:
                add(*jp, jp[0] - xi, 3)
            jp = scan_S(xi, yi)
            if jp:
                add(*jp, jp[1] - yi, 4)
            jp = scan_SW(xi, yi)
            if jp:
                add(*jp, xi - jp[0], 5)
            jp = scan_W(xi, yi)
            if jp:
                add(*jp, xi - jp[0], 6)
            jp = scan_NW(xi, yi)
            if jp:
                add(*jp, xi - jp[0], 7)

        f = (
            expand_N,
            expand_NE,
            expand_E,
            expand_SE,
            expand_S,
            expand_SW,
            expand_W,
            expand_NW,
            expand_all
        )

        for subqueue in queue:
            for xi, yi, d in subqueue:
                if xi == x and yi == y:
                    break
                f[d](xi, yi)
            else:
                continue
            break
        else:
            return

        self.path = [start]
        path: list[Position] = self.path
        while True:
            xi, yi = path[-1]
            if g[yi][xi]:
                path.append(Position(*par[yi][xi]))
            else:
                break
