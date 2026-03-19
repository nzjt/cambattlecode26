from cambc import *
from TileManager import TileManager
from consts import *


class AStar:
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
    H: list[list[int]] = []
    
    @staticmethod
    def precomp(W: int, H: int, x: int, y: int):
        AStar.H = [[max(abs(xi - x), abs(yi - y)) for xi in range(W)] for yi in range(H)]

    def __init__(self, tile_manager: TileManager, W: int, H: int):
        self.tile_manager = tile_manager
        INF = AStar.INF
        self.g: list[list[int]] = [[INF if e else -1 for e in row] for row in self.tile_manager.env_grid]
        self.path: list[Position] = []

    def compute(self, start: Position, end: Position):
        env_grid = self.tile_manager.env_grid
        INF = AStar.INF
        g = self.g
        H = AStar.H

        queue: list[list[tuple[int, int, int]]] = [[], [], []]
        x, y = end
        temp = env_grid[y][x]
        env_grid[y][x] = 1
        xi, yi = start
        g[yi][xi] = 0
        i = H[yi][xi] % 3
        queue[i].append((xi, yi, 8))

        def to_O(xi, yi):
            gj = g[yi][xi] + 1

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 0))

            xi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 1))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 2))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 3))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 4))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 5))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 6))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 7))

        def to_N(xi, yi):
            gj = g[yi][xi] + 1

            xi -= 1
            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 7))

            xi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 0))

            xi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 1))

        def to_NE(xi, yi):
            gj = g[yi][xi] + 1

            xi -= 1
            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 7))

            xi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 0))

            xi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 1))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 2))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 3))

        def to_E(xi, yi):
            gj = g[yi][xi] + 1

            xi += 1
            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 1))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 2))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 3))

        def to_SE(xi, yi):
            gj = g[yi][xi] + 1

            xi += 1
            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 1))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 2))

            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 3))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 4))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 5))

        def to_S(xi, yi):
            gj = g[yi][xi] + 1

            xi += 1
            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 3))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 4))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 5))

        def to_SW(xi, yi):
            gj = g[yi][xi] + 1

            xi += 1
            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 3))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 4))

            xi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 5))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 6))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 7))

        def to_W(xi, yi):
            gj = g[yi][xi] + 1

            xi -= 1
            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 5))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 6))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 7))

        def to_NW(xi, yi):
            gj = g[yi][xi] + 1

            xi -= 1
            yi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 5))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 6))

            yi -= 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 7))

            xi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 0))

            xi += 1
            if gj < g[yi][xi]:
                g[yi][xi] = gj
                queue[(gj + H[yi][xi]) % 3].append((xi, yi, 1))

        f = [
            to_N,
            to_NE,
            to_E,
            to_SE,
            to_S,
            to_SW,
            to_W,
            to_NW,
            to_O
        ]

        while True:
            for xi, yi, d in queue[i]:
                if xi == x and yi == y:
                    env_grid[y][x] = temp
                    return

                f[d](xi, yi)

            queue[i] = []
            i = (i + 1) % 3

    def find_path(self, pos: Position):
        self.path = [pos]
        path = self.path
        print(path)
        g = self.g
        DIRECTIONS = AStar.DIRECTIONS

        if not g[pos.y][pos.x]:
            return

        prev: Direction = Direction.NORTH
        while True:
            mn = pos.add(prev)
            mn_g = g[mn.y][mn.x]
            if mn_g == -1:
                mn_g = AStar.INF
            for d in DIRECTIONS:
                cur = pos.add(d)
                gi = g[cur.y][cur.x]
                if 0 <= gi < mn_g:
                    mn = cur
                    mn_g = gi
                    prev = d

            path.append(pos := mn)
            if not mn_g:
                break
