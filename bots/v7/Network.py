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

        self.adj: list[list[int]] = []
        self.orphans: list[int] = []
        self.childless: list[int] = []

    def update(self):
        W: int = C.W
        nxt: list[int] = self.nxt
        adj = self.adj = [[] for _ in range(W * C.H)]
        for i in range(W * C.H):
            j: int = nxt[i]
            if j >= 0:
                adj[j].append(i)
        self.orphans = [i for i in range(W * C.H) if adj[i] and nxt[i] == -1]
        self.childless = [i for i in range(W * C.H) if nxt[i] == -2]
