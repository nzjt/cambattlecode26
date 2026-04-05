from Nav import *
from TileManager import TileManager
from AStarJPSOptimised import AStarJPSOptimised
import utils as U
from Bfs import Bfs


class AStarNav(Nav):
    def __init__(self, tile_manager: TileManager, bfs: Bfs):
        self.tile_manager: TileManager = tile_manager
        self.bfs: Bfs = bfs

    def move(self, c: Controller, target: Position, movement: Movement) -> None:
        print(target)
        if c.get_move_cooldown():
            return

        a_star: AStarJPSOptimised = AStarJPSOptimised(self.tile_manager, 1)
        g: list[list[int]] = a_star.g
        for pos, lo, hi in self.tile_manager.bot_tracker.values():
            if hi - lo >= 2:
                x, y = pos
                g[y][x] = -1
        a_star.c = c
        a_star.compute(c.get_position(), [target])

        if not a_star.path:
            U.debug("No path!")
            return

        x, y = c.get_position()
        path: list[Position] = U.normalise(a_star.path, 16)
        for i in range(1, len(path)):
            c.draw_indicator_line(path[i - 1], path[i], 255, 0, 128)
        prefix: list[tuple[int, int]] = [(path[i][0] - x, path[i][1] - y) for i in range(1, len(path))]

        unitless: int = ~(self.tile_manager.ally | self.tile_manager.enemy)
        d: Direction = self.bfs.bfs_along_path(prefix, self.tile_manager.pass_ & unitless)

        if d is None:
            if movement.is_rich:
                d: Direction = self.bfs.bfs_along_path(prefix, (self.tile_manager.pass_ | self.tile_manager.buildable) & unitless)

                if d is None:
                    # Cannot :(
                    return
            else:
                return

        movement.move(d)
