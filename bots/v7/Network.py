import consts as C
from cambc import *


class Network:
    def __init__(self, home: Position):
        W, H = C.W, C.H
        nxt = self.nxt = [-1] * (W * H)

        x, y = home
        index: int = y * W + x
        nxt[index] = -2
        nxt[index - W - 1] = -2
        nxt[index - W] = -2
        nxt[index - W + 1] = -2
        nxt[index - 1] = -2
        nxt[index + 1] = -2
        nxt[index + W - 1] = -2
        nxt[index + W] = -2
        nxt[index + W + 1] = -2

        self.adj: list[list[int]] = [[] for _ in range(W * H)]
        self.orphans: list[int] = []
        self.childless: list[int] = []
        self.bad: list[bool] = []

    def update(self, c: Controller):
        t0 = c.get_cpu_time_elapsed()
        W: int = C.W
        nxt: list[int] = self.nxt
        adj: list[list[int]] = self.adj

        bad = self.bad = [i < 0 for i in nxt]

        queue: list[int] = [i for i in range(W * C.H) if (j := nxt[i]) == -1 or j == -3]
        for i in queue:
            for j in adj[i]:
                if not bad[j]:
                    bad[j] = True
                    queue.append(j)

        self.orphans = [i for i in range(W * C.H) if adj[i] and ((j := nxt[i]) == -1 or j >= 0 and nxt[j] == -3)]
        self.childless = [i for i in range(W * C.H) if nxt[i] == -2]
        print(c.get_cpu_time_elapsed() - t0, "update network")
