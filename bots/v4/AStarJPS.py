from cambc import *
from TileManager import TileManager
from consts import *


class AStarJPS:
    INF = 1000000
    DIRECTIONS = (
        Direction.NORTH,
        Direction.EAST,
        Direction.SOUTH,
        Direction.WEST,
        Direction.NORTHEAST,
        Direction.SOUTHEAST,
        Direction.SOUTHWEST,
        Direction.NORTHWEST
    )

    def __init__(self, tile_manager: TileManager):
        self.tile_manager = tile_manager
        INF = AStarJPS.INF
        self.g: list[list[int]] = [[INF if e == 2 else -1 for e in row] for row in self.tile_manager.env_grid]
        self.par: list[list[tuple[int, int] | None]] = [[None] * len(self.g[0]) for _ in range(len(self.g))]
        self.path: list[Position] = []

    def compute(self, start: Position, end: Position):
        env_grid = self.tile_manager.env_grid
        g = self.g
        par = self.par

        queue: list[list[tuple[int, int, int]]] = [[] for _ in range(500)]
        x, y = end
        env_grid[y][x] = 1
        xi, yi = start
        g[yi][xi] = 0

        def add(xj: int, yj: int, gi: int, d: int):
            if gi < g[yj][xj]:
                g[yj][xj] = gi
                queue[g[yj][xj] + max(abs(xj - x), abs(yj - y))].append((xj, yj, d))
                par[yj][xj] = (xi, yi)

        def scan_N(xj, yj) -> tuple[int, int] | None:
            while True:
                yj -= 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj][xj - 1] == -1 and g[yj - 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj - 1][xj + 1] != -1:
                    return xj, yj

        def scan_E(xj, yj) -> tuple[int, int] | None:
            while True:
                xj += 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj - 1][xj] == -1 and g[yj - 1][xj + 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj + 1] != -1:
                    return xj, yj

        def scan_S(xj, yj) -> tuple[int, int] | None:
            while True:
                yj += 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj][xj - 1] == -1 and g[yj + 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj + 1][xj + 1] != -1:
                    return xj, yj

        def scan_W(xj, yj) -> tuple[int, int] | None:
            while True:
                xj -= 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj - 1][xj] == -1 and g[yj - 1][xj - 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj - 1] != -1:
                    return xj, yj

        def scan_NE(xj, yj) -> tuple[int, int] | None:
            while True:
                xj += 1
                yj -= 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj][xj - 1] == -1 and g[yj - 1][xj - 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj + 1] != -1:
                    return xj, yj
                if scan_N(xj, yj) or scan_E(xj, yj):
                    return xj, yj

        def scan_SE(xj, yj) -> tuple[int, int] | None:
            while True:
                xj += 1
                yj += 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj - 1][xj] == -1 and g[yj - 1][xj + 1] != -1 or g[yj][xj - 1] == -1 and g[yj + 1][xj - 1] != -1:
                    return xj, yj
                if scan_E(xj, yj) or scan_S(xj, yj):
                    return xj, yj

        def scan_SW(xj, yj) -> tuple[int, int] | None:
            while True:
                xj -= 1
                yj += 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj][xj + 1] == -1 and g[yj + 1][xj + 1] != -1 or g[yj - 1][xj] == -1 and g[yj - 1][xj - 1] != -1:
                    return xj, yj
                if scan_S(xj, yj) or scan_W(xj, yj):
                    return xj, yj

        def scan_NW(xj, yj) -> tuple[int, int] | None:
            while True:
                xj -= 1
                yj -= 1
                if xj == x and yj == y:
                    return xj, yj
                if g[yj][xj] == -1:
                    return
                if g[yj + 1][xj] == -1 and g[yj + 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj - 1][xj + 1] != -1:
                    return xj, yj
                if scan_W(xj, yj) or scan_N(xj, yj):
                    return xj, yj

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

        def expand_N(xi, yi):
            gi = g[yi][xi]

            jp = scan_N(xi, yi)
            if jp:
                add(*jp, gi + yi - jp[1], 0)
            if g[yi][xi - 1] == -1:
                jp = scan_NW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 7)
            if g[yi][xi + 1] == -1:
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
            if g[yi][xi - 1] == -1:
                jp = scan_NW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 7)
            if g[yi + 1][xi] == -1:
                jp = scan_SE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 3)

        def expand_E(xi, yi):
            gi = g[yi][xi]

            jp = scan_E(xi, yi)
            if jp:
                add(*jp, gi + jp[0] - xi, 2)
            if g[yi - 1][xi] == -1:
                jp = scan_NE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 1)
            if g[yi + 1][xi] == -1:
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
            if g[yi - 1][xi] == -1:
                jp = scan_NE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 1)
            if g[yi][xi - 1] == -1:
                jp = scan_SW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 5)

        def expand_S(xi, yi):
            gi = g[yi][xi]

            jp = scan_S(xi, yi)
            if jp:
                add(*jp, gi + jp[1] - yi, 4)
            if g[yi][xi + 1] == -1:
                jp = scan_SE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 3)
            if g[yi][xi - 1] == -1:
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
            if g[yi][xi + 1] == -1:
                jp = scan_SE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 3)
            if g[yi - 1][xi] == -1:
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
            if g[yi + 1][xi] == -1:
                jp = scan_SW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 5)
            if g[yi - 1][xi] == -1:
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
            if g[yi + 1][xi] == -1:
                jp = scan_SW(xi, yi)
                if jp:
                    add(*jp, gi + xi - jp[0], 5)
            if g[yi][xi + 1] == -1:
                jp = scan_NE(xi, yi)
                if jp:
                    add(*jp, gi + jp[0] - xi, 1)

        f = [
            expand_N,
            expand_NE,
            expand_E,
            expand_SE,
            expand_S,
            expand_SW,
            expand_W,
            expand_NW
        ]

        for i in range(max(abs(xi - x), abs(yi - y)), 500):
            for xi, yi, d in queue[i]:
                if xi == x and yi == y:
                    break
                f[d](xi, yi)
            else:
                continue
            break

        self.path = [end]
        path: list[Position] = self.path
        while path[-1] != start:
            xi, yi = path[-1]
            path.append(Position(*par[yi][xi]))
