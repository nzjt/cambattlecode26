from cambc import *
import consts as C


def find(x: int, par: list[int]):
    p: int = par[x]
    if p == x:
        return x
    par[x] = p = find(p, par)
    return p

class DynamicConnectivity:
    def __init__(self):
        self.par: list[int] = list(range(C.W * C.H))
        self.count: list[int] = [0] * (C.W * C.H)
        self.harvesters: set[int] = set()

    def merge(self, a: int, b: int):
        par: list[int] = self.par
        c: int = find(a, par)
        d: int = find(b, par)
        if c != d:
            par[d] = c
            count: list[int] = self.count
            count[c] += count[d]

    def add_harvester(self, i: int):
        harvesters: set[int] = self.harvesters
        if i not in harvesters:
            harvesters.add(i)
            self.count[find(i, self.par)] += 1
