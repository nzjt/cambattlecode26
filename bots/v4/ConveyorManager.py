from os import environ

from cambc import *
from AStarJPSOptimised import AStarJPSOptimised
from TileManager import TileManager
from Movement import Movement
from Bfs import Bfs
from utils import *
from consts import *
from Nav import Nav


class ConveyorManager:
    BUILD_BARRIER = {
        Environment.EMPTY,
        Environment.ORE_AXIONITE
    }

    def __init__(self, c: Controller, tile_manager: TileManager, start: Position, target: Position, nav: Nav):
        W: int = c.get_map_width()

        a_star: AStarJPSOptimised = AStarJPSOptimised(tile_manager)
        x, y = start
        g: list[list[int]] = a_star.g
        blocked_N: bool = g[y - 1][x] == -1
        blocked_E: bool = g[y][x + 1] == -1
        blocked_S: bool = g[y + 1][x] == -1
        blocked_W: bool = g[y][x - 1] == -1
        if blocked_N and blocked_E:
            g[y - 1][x + 1] = -1
        if blocked_E and blocked_S:
            g[y + 1][x + 1] = -1
        if blocked_S and blocked_W:
            g[y + 1][x - 1] = -1
        if blocked_W and blocked_N:
            g[y - 1][x - 1] = -1

        a_star.compute(start, [target], True)

        if a_star.path:
            path = self.path = normalise_on_grid(a_star.path, tile_manager.env_grid)
            self.path_index: list[list[bool]] | None = None
            self.index_path(c)

            self.index = 1
            self.done: bool = False
            for i in range(1, len(path)):
                c.draw_indicator_line(path[i - 1], path[i], 255, 0, 255)

            self.launcher_index: int = 1

            self.nav: Nav = nav
        else:
            self.path = []

    def index_path(self, c: Controller):
        path: list[Position] = self.path
        W, H = c.get_map_width(), c.get_map_height()
        path_index = self.path_index = [[1000000] * (W + 1) for _ in range(H + 1)]
        for i in range(len(path)):
            x, y = path[i]
            path_index[y][x] = i

    def retarget(self, c: Controller, retargets: list[Position], tile_manager: TileManager):
        x, y = c.get_position()
        lo, hi = self.index, self.index
        xi, yi = self.path[hi]
        dx, dy = xi - x, yi - y
        if -4 <= dx <= 4 and -4 <= dy <= 4:
            goal: int = 1 << (dx + dy * 10 + 44)
        else:
            # ???
            return

        while lo > 1:
            xi, yi = self.path[lo - 1]
            dx, dy = xi - x, yi - y
            if -4 <= dx <= 4 and -4 <= dy <= 4:
                goal |= 1 << (dx + dy * 10 + 44)
                lo -= 1
            else:
                break

        retarget_set: int = 0
        for xi, yi in retargets:
            dx, dy = xi - x, yi - y
            if -4 <= dx <= 4 and -4 <= dy <= 4:
                retarget_set |= 1 << (dx + dy * 10 + 44)

        raw_path: list[tuple[int, int]] = Bfs.closest_start(goal, retarget_set, (tile_manager.pass_ | tile_manager.buildable | tile_manager.barrier) & ~tile_manager.ore)
        if not raw_path:
            return

        suffix: list[Position] = [Position(x + dx, y + dy) for dx, dy in raw_path]
        suffix = normalise_on_grid(suffix, tile_manager.env_grid)
        if len(suffix) < len(self.path) - self.index:
            while self.path[self.index] != suffix[0]:
                self.index -= 1
            self.path = self.path[:self.index]

            self.path += suffix

            for i in range(1, len(self.path)):
                c.draw_indicator_line(self.path[i - 1], self.path[i], 255, 255, 0)

            self.index_path(c)

    def update(self, c: Controller, movement: Movement, tile_manager: TileManager, bfs: Bfs, repair: bool = False, wait: bool = False):
        my_id = c.get_id()
        my_team = c.get_team()
        my_pos = c.get_position(my_id)
        on_ore: bool = not repair and my_pos == self.path[0]
        W, H = c.get_map_width(), c.get_map_height()
        enemy_near: bool = False
        for bb_id in c.get_nearby_units(8):
            if c.get_team(bb_id) != my_team:
                enemy_near = True
                break

        def build_barriers() -> bool:
            pos: Position = self.path[0]
            for e in CARDINAL:
                cur = pos.add(e)
                if 0 <= cur.x < W and 0 <= cur.y < H:
                    if self.path_index[cur.y][cur.x] == 1000000 and c.get_tile_env(cur) != Environment.WALL:
                        building_id = c.get_tile_building_id(cur)
                        if c.get_team(building_id) == my_team:
                            if building_id is None or c.get_entity_type(building_id) in UNIMPORTANT:
                                if c.get_action_cooldown() or c.get_global_resources()[0] < c.get_barrier_cost()[0]:
                                    return False
                                if c.get_tile_builder_bot_id(cur) is not None:
                                    return False
                                if cur.distance_squared(my_pos) > 2:
                                    return False
                                if c.can_destroy(cur):
                                    c.destroy(cur)
                                c.build_barrier(cur)
                        else:
                            if not enemy_near:
                                if cur.distance_squared(my_pos) <= 2:
                                    d: Direction = my_pos.direction_to(cur)
                                    if not movement.can_move(d):
                                        return False
                                else:
                                    d: Direction = bfs.bfs_to_pos(cur.x - my_pos.x, cur.y - my_pos.y, tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy)
                                if d is not None:
                                    if not c.get_move_cooldown():
                                        movement.move(d)
                            if c.can_fire(cur):
                                c.fire(cur)
                            return False

            return True

        if not on_ore:
            dist = my_pos.distance_squared(self.path[0])
            if dist <= 13:
                building_id = c.get_tile_building_id(self.path[0])
                if c.get_entity_type(building_id) != EntityType.HARVESTER:
                    if dist == 1:
                        building_id = c.get_tile_building_id(my_pos)
                        if c.get_team(building_id) != my_team and not enemy_near:
                            if c.can_fire(my_pos):
                                c.fire(my_pos)
                            return

                    if dist <= 2:
                        if c.get_action_cooldown():
                            return

                        d: Direction = my_pos.direction_to(self.path[0])
                        if not c.get_move_cooldown() and (c.can_move(d) or c.get_global_resources()[0] >= c.get_road_cost()[0]):
                            if c.can_destroy(self.path[0]):
                                c.destroy(self.path[0])
                            if c.can_build_road(self.path[0]):
                                c.build_road(self.path[0])
                            movement.move(d)
                            on_ore = True
                        else:
                            return
                    else:
                        self.nav.move(c, self.path[0], movement)
                        return

        do_build: bool = False
        if on_ore:
            if wait:
                return

            pos: Position = self.path[1]
            do_build = True
            if not build_barriers():
                return

            building_id = c.get_tile_building_id(pos)
            if c.get_entity_type(building_id) in CONVEYOR_VARIANT and c.get_team(building_id) == my_team:
                if movement.can_move(my_pos.direction_to(pos)) and not c.get_action_cooldown():
                    if c.get_global_resources()[0] >= c.get_harvester_cost()[0]:
                        movement.move(my_pos.direction_to(pos))
                        if c.can_destroy(self.path[0]):
                            c.destroy(self.path[0])

                        c.build_harvester(self.path[0])
                return

        if my_pos.distance_squared(self.path[0]) <= 13:
            mine: list[bool] = [False] * 4
            enemy: list[bool] = [False] * 4
            turret: list[bool] = [False] * 4
            for i in range(4):
                d: Direction = CARDINAL[i]
                cur = self.path[0].add(d)
                if c.get_tile_env(cur) == Environment.WALL:
                    continue
                building_id = c.get_tile_building_id(cur)
                e_type = c.get_entity_type(building_id)
                if c.get_team(building_id) == my_team or e_type == EntityType.MARKER:
                    bb_id = c.get_tile_builder_bot_id(cur)
                    mine[i] = bb_id is None or bb_id == my_id
                else:
                    enemy[i] = True
                    turret[i] = e_type in TURRET

            for i in range(4):
                if turret[i]:
                    if mine[i - 1]:
                        # building_id = c.get_tile_building_id(self.path[0].add(CARDINAL[i]))
                        # d: Direction = self.path[0].add(CARDINAL[i]).direction_to(self.path[0].add(CARDINAL[i - 1]))
                        # if abs()
                        j = i - 1
                    elif mine[i + 1]:
                        j = (i + 1) % 4
                    else:
                        continue

                    cur = self.path[0].add(CARDINAL[j])
                    building_id = c.get_tile_building_id(cur)
                    d: Direction = cur.direction_to(self.path[0].add(CARDINAL[i]))
                    if building_id is not None and c.get_entity_type(building_id) == EntityType.GUNNER:
                        if c.get_direction(building_id) == d:
                            continue

                    dist = my_pos.distance_squared(cur)
                    if not dist:
                        for d in DIRECTIONS:
                            if movement.can_move(d):
                                movement.move(d)
                                my_pos = c.get_position()
                                dist = my_pos.distance_squared(cur)
                                break

                    if 1 <= dist <= 2:
                        if c.get_global_resources()[0] >= c.get_gunner_cost()[0] and not c.get_action_cooldown():
                            if c.can_destroy(cur):
                                c.destroy(cur)
                            c.build_gunner(cur, d)
                    else:
                        self.nav.move(c, cur, movement)
                    return

        protected = tile_manager.protected
        while self.launcher_index < len(self.path) - 1:
            xi, yi = self.path[self.launcher_index]
            if protected[yi][xi]:
                self.launcher_index += 1
            else:
                break

        if self.index >= self.launcher_index + 1:
            pos = self.path[self.launcher_index]
            dist = my_pos.distance_squared(pos)
            if dist > 2:
                self.nav.move(c, pos, movement)
                my_pos = c.get_position()
                dist = my_pos.distance_squared(pos)

            if dist <= 2 and c.get_global_resources()[0] >= c.get_launcher_cost()[0] and not c.get_action_cooldown():
                best: Position | None = None
                mx: int = 0
                destroy: Position | None = None
                for d in DIRECTIONS:
                    cur = pos.add(d)
                    if 0 <= cur.x < W and 0 <= cur.y < H:
                        building_id = c.get_tile_building_id(cur)
                        e_type = c.get_entity_type(building_id)
                        if c.get_team(building_id) != my_team:
                            if e_type in DESTROY_ENEMY:
                                destroy = cur
                            continue
                        if building_id is not None and e_type not in CAN_BUILD_LAUNCHER:
                            continue
                        if c.get_tile_env(cur) != Environment.EMPTY:
                            continue
                        xi, yi = cur
                        if self.path_index[yi][xi] != 1000000:
                            continue
                        i = self.launcher_index
                        while i < len(self.path) - 1 and cur.distance_squared(self.path[i]) <= 2:
                            i += 1
                        if i > mx:
                            best = cur
                            mx = i

                if best is None:
                    if destroy is not None:
                        if my_pos != destroy:
                            self.nav.move(c, destroy, movement)
                            my_pos = c.get_position()

                        if my_pos == destroy:
                            if c.can_fire(my_pos):
                                c.fire(my_pos)
                    return
                else:
                    if dist:
                        self.nav.move(c, pos, movement)
                        my_pos = c.get_position()

                    if my_pos == pos and not c.get_action_cooldown() and c.get_tile_builder_bot_id(best) is None:
                        if c.can_destroy(best):
                            c.destroy(best)
                        c.build_launcher(best)
                        self.launcher_index = mx
                    return
            else:
                return

        if self.index == len(self.path) - 1:
            # Special case where ore is adjacent to conveyor
            if len(self.path) == 2:
                dist = my_pos.distance_squared(self.path[0])
                if dist == 0:
                    if c.get_global_resources()[0] >= c.get_harvester_cost()[0]:
                        if not c.get_move_cooldown() and not c.get_action_cooldown():
                            for d in DIRECTIONS:
                                if c.can_move(d):
                                    movement.move(d)

                                    if c.can_destroy(my_pos):
                                        c.destroy(my_pos)
                                    if c.can_build_harvester(my_pos):
                                        c.build_harvester(my_pos)
                                        self.done = True

                                    return

                            for d in DIRECTIONS:
                                cur = my_pos.add(d)
                                if c.can_build_road(cur):
                                    c.build_road(cur)
                    return
                elif dist <= 2:
                    if c.get_global_resources()[0] >= c.get_harvester_cost()[0]:
                        if not c.get_action_cooldown():
                            if c.can_destroy(self.path[0]):
                                c.destroy(self.path[0])
                            c.build_harvester(self.path[0])
                            self.done = True
                            return
                    d: Direction = my_pos.direction_to(self.path[0])
                    if movement.can_move(d):
                        movement.move(d)
            else:
                self.done = not on_ore
            return

        pos: Position = self.path[self.index]
        if not c.is_in_vision(pos):
            self.nav.move(c, pos, movement)
            return

        building_id = c.get_tile_building_id(pos)
        if c.get_entity_type(building_id) == EntityType.GUNNER and c.get_team(building_id) == my_team:
            keep_gunner: bool = False
            di: Direction = c.get_direction(building_id)
            cur: Position = pos
            for _ in range(3 if di in CARDINAL else 2):
                cur = cur.add(di)
                if 0 <= cur.x < W and 0 <= cur.y < H and c.get_tile_env(cur) != Environment.WALL:
                    building_id = c.get_tile_building_id(cur)
                    if building_id is not None and c.get_entity_type(building_id) != EntityType.MARKER:
                        keep_gunner = c.get_team(building_id) != my_team
                        break
                else:
                    break

            if keep_gunner:
                if my_pos != self.path[self.index - 1]:
                    self.nav.move(c, self.path[self.index - 1], movement)
                return
            else:
                if c.can_destroy(pos):
                    c.destroy(pos)
                else:
                    xi, yi = pos
                    d: Direction = bfs.bfs_to_pos(xi - my_pos.x, yi - my_pos.y, tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy)
                    if d is not None and d != Direction.CENTRE:
                        movement.move(d)

                    if c.can_destroy(pos):
                        c.destroy(pos)
                    else:
                        return

        building_id = c.get_tile_building_id(pos)
        e_type = c.get_entity_type(building_id)
        need_gunner = c.get_team(building_id) != my_team and e_type != EntityType.MARKER
        if need_gunner:
            if e_type in DESTROY_ENEMY:
                if my_pos != pos:
                    self.nav.move(c, pos, movement)
                if c.can_fire(pos):
                    c.fire(pos)
                return
            else:
                self.index -= 1
                if not self.index:
                    return
                pos = self.path[self.index]
        else:
            nxt = self.path[self.index + 1]
            need_gunner = c.is_in_vision(nxt)
            if need_gunner:
                building_id = c.get_tile_building_id(nxt)
                need_gunner &= c.get_team(building_id) != my_team and c.get_entity_type(building_id) not in DESTROY_ENEMY
        nxt = self.path[self.index + 1]

        if my_pos.distance_squared(pos) <= 2:
            d: Direction = pos.direction_to(nxt)
            if need_gunner:
                if c.get_global_resources()[0] >= c.get_gunner_cost()[0]:
                    pass_: int = tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy
                    d: Direction = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
                    if d is not None and d != Direction.CENTRE:
                        movement.move(d)

                    if c.can_destroy(pos):
                        c.destroy(pos)

                    if c.can_build_gunner(pos, d):
                        c.build_gunner(pos, d)
            else:
                if not c.get_move_cooldown() and not c.get_action_cooldown():
                    dx, dy = d.delta()
                    if dx and dy:
                        if c.can_destroy(pos):
                            c.destroy(pos)

                        if c.get_global_resources()[0] >= c.get_bridge_cost()[0]:
                            c.build_bridge(pos, nxt)
                            self.index += 1
                    else:
                        if c.can_destroy(pos):
                            c.destroy(pos)

                        if c.get_global_resources()[0] >= c.get_conveyor_cost()[0]:
                            c.build_conveyor(pos, d)
                            self.index += 1

                        if do_build:
                            return

                    pass_: int = tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy
                    d: Direction = bfs.bfs_to_pos(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
                    if d is None or d != Direction.CENTRE and not c.can_move(d):
                        d = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, pass_)

                    if d is not None and d != Direction.CENTRE:
                        movement.move(d)
        else:
            if do_build:
                return

            pass_: int = tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy
            d: Direction = bfs.bfs_to_pos(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
            if d is None or d != Direction.CENTRE and not c.can_move(d):
                d = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, pass_)

            if d is not None and d != Direction.CENTRE:
                print(pos)
                movement.move(d)
