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

    def __init__(self, tile_manager: TileManager):
        self.tile_manager = tile_manager
        INF = AStar.INF
        self.g: list[list[int]] = [[INF if e == 2 else -1 for e in row] for row in self.tile_manager.env_grid]
        self.path: list[Position] = []

    def compute(self, start: Position, end: Position):
        env_grid = self.tile_manager.env_grid
        INF = AStar.INF
        g = self.g

        queue: list[list[tuple[int, int]]] = [[], [], []]
        x, y = start
        temp = env_grid[y][x]
        env_grid[y][x] = 1
        xi, yi = end
        g[yi][xi] = 0
        i = max(abs(xi - x), abs(yi - y)) % 3
        queue[i].append((xi, yi))
        while True:
            for xi, yi in queue[i]:
                if xi == x and yi == y:
                    env_grid[y][x] = temp
                    return
                gj = g[yi][xi] + 1

                yi -= 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

                xi += 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

                yi += 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

                yi += 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

                xi -= 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

                xi -= 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

                yi -= 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

                yi -= 1
                if gj < g[yi][xi]:
                    g[yi][xi] = gj
                    queue[(gj + max(abs(xi - x), abs(yi - y))) % 3].append((xi, yi))

            queue[i] = []
            i = (i + 1) % 3

    def find_path(self, pos: Position):
        self.path = [pos]
        path = self.path
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
