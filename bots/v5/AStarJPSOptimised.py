from cambc import *
from TileManager import TileManager
import consts as C


class AStarJPSOptimised:
    INF = 1000000

    def __init__(self, tile_manager: TileManager, mode: int = 0):
        self.tile_manager = tile_manager
        INF = AStarJPSOptimised.INF
        if mode == 0:
            # Conveyor nav
            self.g: list[list[int]] = [[INF if e == 2 else -1 for e in row] for row in self.tile_manager.env_grid]
        else:
            # Bot nav
            self.g: list[list[int]] = [[INF if p else -1 for p in row] for row in self.tile_manager.pass_grid]

        for row in self.g:
            row.append(-1)
        self.g.append([-1] * len(self.g[0]))
        self.par: list[list[tuple[int, int] | None]] = [[None] * len(self.g[0]) for _ in range(len(self.g))]
        self.path: list[Position] = []

    def compute(self, start: Position, end: list[Position], is_core: bool = False):
        g = self.g
        par = self.par

        queue: list[list[tuple[int, int, int]]] = [[] for _ in range(200)]
        x, y = start
        g[y][x] = AStarJPSOptimised.INF

        def add_source(xj: int, yj: int, d: int):
            g[yj][xj] = 0
            queue[max(abs(xj - x), abs(yj - y))].append((xj, yj, d))

        def add(xj: int, yj: int, gi: int, d: int):
            if gi < g[yj][xj]:
                g[yj][xj] = gi
                queue[g[yj][xj] + max(abs(xj - x), abs(yj - y))].append((xj, yj, d))
                par[yj][xj] = (xi, yi)

        def scan_N_bool(xj, yj) -> bool:
            if xj == x and yj > y:
                while True:
                    yj -= 1
                    if yj == y:
                        return True
                    if g[yj][xj] == -1:
                        return False
                    if g[yj][xj - 1] == -1 and g[yj - 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj - 1][xj + 1] != -1:
                        return True
            else:
                while True:
                    yj -= 1
                    if g[yj][xj] == -1:
                        return False
                    if g[yj][xj - 1] == -1 and g[yj - 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj - 1][xj + 1] != -1:
                        return True

        def scan_E_bool(xj, yj) -> bool:
            if yj == y and xj < x:
                while True:
                    xj += 1
                    if xj == x:
                        return True
                    if g[yj][xj] == -1:
                        return False
                    if g[yj - 1][xj] == -1 and g[yj - 1][xj + 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj + 1] != -1:
                        return True
            else:
                while True:
                    xj += 1
                    if g[yj][xj] == -1:
                        return False
                    if g[yj - 1][xj] == -1 and g[yj - 1][xj + 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj + 1] != -1:
                        return True


        def scan_S_bool(xj, yj) -> bool:
            if xj == x and yj < y:
                while True:
                    yj += 1
                    if yj == y:
                        return True
                    if g[yj][xj] == -1:
                        return False
                    if g[yj][xj - 1] == -1 and g[yj + 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj + 1][xj + 1] != -1:
                        return True
            else:
                while True:
                    yj += 1
                    if g[yj][xj] == -1:
                        return False
                    if g[yj][xj - 1] == -1 and g[yj + 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj + 1][xj + 1] != -1:
                        return True

        def scan_W_bool(xj, yj) -> bool:
            if yj == y and xj > x:
                while True:
                    xj -= 1
                    if xj == x:
                        return True
                    if g[yj][xj] == -1:
                        return False
                    if g[yj - 1][xj] == -1 and g[yj - 1][xj - 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj - 1] != -1:
                        return True
            else:
                while True:
                    xj -= 1
                    if g[yj][xj] == -1:
                        return False
                    if g[yj - 1][xj] == -1 and g[yj - 1][xj - 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj - 1] != -1:
                        return True

        def scan_N(xj, yj) -> tuple[int, int] | None:
            if xj == x and yj > y:
                while True:
                    yj -= 1
                    if yj == y:
                        return xj, yj
                    if g[yj][xj] == -1:
                        return
                    if g[yj][xj - 1] == -1 and g[yj - 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj - 1][xj + 1] != -1:
                        return xj, yj
            else:
                while True:
                    yj -= 1
                    if g[yj][xj] == -1:
                        return
                    if g[yj][xj - 1] == -1 and g[yj - 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj - 1][xj + 1] != -1:
                        return xj, yj

        def scan_E(xj, yj) -> tuple[int, int] | None:
            if yj == y and xj < x:
                while True:
                    xj += 1
                    if xj == x:
                        return xj, yj
                    if g[yj][xj] == -1:
                        return
                    if g[yj - 1][xj] == -1 and g[yj - 1][xj + 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj + 1] != -1:
                        return xj, yj
            else:
                while True:
                    xj += 1
                    if xj == x:
                        return xj, yj
                    if g[yj][xj] == -1:
                        return
                    if g[yj - 1][xj] == -1 and g[yj - 1][xj + 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj + 1] != -1:
                        return xj, yj

        def scan_S(xj, yj) -> tuple[int, int] | None:
            if xj == x and yj < y:
                while True:
                    yj += 1
                    if yj == y:
                        return xj, yj
                    if g[yj][xj] == -1:
                        return
                    if g[yj][xj - 1] == -1 and g[yj + 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj + 1][xj + 1] != -1:
                        return xj, yj
            else:
                while True:
                    yj += 1
                    if g[yj][xj] == -1:
                        return
                    if g[yj][xj - 1] == -1 and g[yj + 1][xj - 1] != -1 or g[yj][xj + 1] == -1 and g[yj + 1][xj + 1] != -1:
                        return xj, yj

        def scan_W(xj, yj) -> tuple[int, int] | None:
            if yj == y and xj > x:
                while True:
                    xj -= 1
                    if xj == x:
                        return xj, yj
                    if g[yj][xj] == -1:
                        return
                    if g[yj - 1][xj] == -1 and g[yj - 1][xj - 1] != -1 or g[yj + 1][xj] == -1 and g[yj + 1][xj - 1] != -1:
                        return xj, yj
            else:
                while True:
                    xj -= 1
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
                if scan_N_bool(xj, yj) or scan_E_bool(xj, yj):
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
                if scan_E_bool(xj, yj) or scan_S_bool(xj, yj):
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
                if scan_S_bool(xj, yj) or scan_W_bool(xj, yj):
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
                if scan_W_bool(xj, yj) or scan_N_bool(xj, yj):
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

        f = (
            expand_N,
            expand_NE,
            expand_E,
            expand_SE,
            expand_S,
            expand_SW,
            expand_W,
            expand_NW
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
