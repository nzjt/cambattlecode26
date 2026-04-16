import random
from cambc import *
from AStarJPSOptimised import AStarJPSOptimised
from TileManager import TileManager
from Movement import Movement
from Bfs import Bfs
import utils as U
import consts as C
from Nav import Nav


class ConveyorManager:
    BUILD_BARRIER = {
        Environment.EMPTY,
        Environment.ORE_AXIONITE
    }

    def __init__(self, nav: Nav, home: Position):
        self.mode: int = 0  # 0: avoid joining, 1: normal, 2: axionite
        self.path_index: list[list[bool]] | None = None
        self.path = []
        self.index = 1
        self.done: bool = False
        self.nav: Nav = nav
        self.home: Position = home
        self.splitter: Position | None = None
        self.conveyor: Position | None = None

    def compute(self, c: Controller, tile_manager: TileManager, start: Position, avoid_joining: bool, is_harvester: bool = True):
        if avoid_joining:
            a_star: AStarJPSOptimised = AStarJPSOptimised(tile_manager, 0)
            g: list[list[int]] = a_star.g
            if c.get_current_round() >= 100:
                x, y = self.home
                env_grid = tile_manager.env_grid
                if env_grid[y - 2][x + 2] == 3:
                    g[y - 2][x + 2] = 1000000
                if env_grid[y + 2][x + 2] == 3:
                    g[y + 2][x + 2] = 1000000
                if env_grid[y - 2][x - 2] == 3:
                    g[y - 2][x - 2] = 1000000
                if env_grid[y + 2][x - 2] == 3:
                    g[y + 2][x - 2] = 1000000
        else:
            self.mode = 1
            a_star: AStarJPSOptimised = AStarJPSOptimised(tile_manager, 1)
            g: list[list[int]] = a_star.g

        # TODO: replace with BFS
        if is_harvester:
            my_team = c.get_team()
            ban: list[tuple[int, int]] = []
            for d in C.DIRECTIONS:
                cur: Position = start.add(d)
                if U.on_the_map(cur):
                    building_id = c.get_tile_building_id(cur)
                    if c.get_team(building_id) != my_team:
                        if c.get_entity_type(building_id) not in C.DESTROY_ENEMY:
                            xi, yi = cur
                            g[yi][xi] = -1
                            ban.append((xi, yi))
            x, y = start
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

        a_star.compute(start, [self.home], True)
        return a_star.path

    def compute_to_conveyors(self, tile_manager: TileManager, start: Position):
        self.mode = 2

        W_plus_1: int = C.W + 1
        pass_: int = tile_manager["empty"]

        # Can't be adj to two walls
        wall_N: int = ~(pass_ << W_plus_1)
        wall_E: int = ~(pass_ >> 1)
        wall_S: int = ~(pass_ >> W_plus_1)
        wall_W: int = ~(pass_ << 1)
        too_walled: int = wall_N & wall_E | wall_N & wall_S | wall_N & wall_W | wall_E & wall_S | wall_E & wall_W | wall_S & wall_W

        titanium: int = tile_manager["titanium"]
        pass_ &= ~(titanium << 1 | titanium >> 1 | titanium << W_plus_1 | titanium >> W_plus_1)

        x, y = start
        bit: int = 1 << (y * W_plus_1 + x)
        adj = (bit << 1 | bit >> 1 | bit << W_plus_1 | bit >> W_plus_1) & pass_
        if not adj:
            return []

        seen: list[int] = [tile_manager["conveyor"]]
        if seen[0] & adj:
            return []

        while len(seen) < 100:
            cur: int = seen[-1]
            cur |= cur << 1 | cur >> 1 | cur << W_plus_1 | cur >> W_plus_1

            if len(seen) >= 3:
                prev: int = seen[-2]
                prev |= prev << 1 | prev >> 1
                cur |= prev | prev << W_plus_1 | prev >> W_plus_1
            elif len(seen) == 1:
                cur &= ~too_walled & ~seen[0]

            cur &= pass_
            seen.append(cur)

            if cur & adj:
                path: list[Position] = [start]
                diagonal: bool = False
                for cur in reversed(seen):
                    if diagonal:
                        if bit >> (W_plus_1 - 1) & cur:
                            start = start.add(Direction.NORTHEAST)
                            bit >>= W_plus_1 - 1
                        elif bit << (W_plus_1 + 1) & cur:
                            start = start.add(Direction.SOUTHEAST)
                            bit <<= W_plus_1 + 1
                        elif bit << (W_plus_1 - 1) & cur:
                            start = start.add(Direction.SOUTHWEST)
                            bit <<= W_plus_1 - 1
                        elif bit >> (W_plus_1 + 1) & cur:
                            start = start.add(Direction.NORTHWEST)
                            bit >>= W_plus_1 + 1
                        diagonal = False
                    else:
                        if bit >> W_plus_1 & cur:
                            start = start.add(Direction.NORTH)
                            bit >>= W_plus_1
                        elif bit << 1 & cur:
                            start = start.add(Direction.EAST)
                            bit <<= 1
                        elif bit << W_plus_1 & cur:
                            start = start.add(Direction.SOUTH)
                            bit <<= W_plus_1
                        elif bit >> 1 & cur:
                            start = start.add(Direction.WEST)
                            bit >>= 1
                        else:
                            diagonal = True
                            continue
                    path.append(start)
                return path

        return []

    def generate_path(self, c: Controller, tile_manager: TileManager, start: Position, mode: int = 0):
        if mode <= 1:
            path = self.compute(c, tile_manager, start, not mode)
        else:
            path = self.compute_to_conveyors(tile_manager, start)
        if path:
            path = self.path = U.normalise_on_grid(path, tile_manager.env_grid)
            self.index_path(c)

            for i in range(1, len(path)):
                c.draw_indicator_line(path[i - 1], path[i], 255, 0, 255)

    def index_path(self, c: Controller):
        path: list[Position] = self.path
        W_plus_1: int = C.W + 1
        path_index = self.path_index = [[1000000] * W_plus_1 for _ in range(C.H + 1)]
        for i in range(len(path)):
            x, y = path[i]
            path_index[y][x] = i

    def retarget(self, c: Controller, retargets: list[Position], tile_manager: TileManager, stuck: bool = False):
        if self.mode == 0:
            path = self.compute(c, tile_manager, self.path[self.index], True, False)
            if path:
                path = U.normalise_on_grid(path, tile_manager.env_grid)
                if len(path) < len(self.path) - self.index:
                    self.path = self.path[:self.index] + path
                    self.index_path(c)
                    for i in range(1, len(path)):
                        c.draw_indicator_line(path[i - 1], path[i], 255, 0, 255)
                    return
            elif stuck:
                self.mode = 1

        if self.mode == 1:  # TODO: allow axionite retarget
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
            suffix = U.normalise_on_grid(suffix, tile_manager.env_grid)
            if len(suffix) < len(self.path) - self.index:
                while self.path[self.index] != suffix[0]:
                    self.index -= 1
                self.path = self.path[:self.index]

                self.path += suffix

                for i in range(1, len(self.path)):
                    c.draw_indicator_line(self.path[i - 1], self.path[i], 255, 255, 0)

                self.index_path(c)

    def update(self, c: Controller, movement: Movement, tile_manager: TileManager, bfs: Bfs, repair: bool = False):
        my_team = c.get_team()
        if c.is_in_vision(self.path[0]):
            building_id = c.get_tile_building_id(self.path[0])
            if c.get_team(building_id) != my_team and c.get_entity_type(building_id) not in C.UNIMPORTANT:
                self.done = True
                return

        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        on_ore: bool = not repair and my_pos == self.path[0]
        enemy_near: bool = False
        for bb_id in c.get_nearby_units(5):
            if c.get_team(bb_id) != my_team:
                if c.get_position(bb_id).distance_squared(self.path[0]) <= 2:
                    enemy_near = True
                    break

        def build_barriers() -> bool:
            pos: Position = self.path[0]
            for e in C.CARDINAL:
                cur = pos.add(e)
                if U.on_the_map(cur):
                    e_type = c.get_tile_env(cur)
                    if self.path_index[cur.y][cur.x] == 1000000 and e_type != Environment.WALL:
                        if e_type == Environment.ORE_TITANIUM:
                            bb_id = c.get_tile_builder_bot_id(cur)
                            if bb_id is not None and bb_id != my_id and c.get_team(bb_id) == my_team:
                                continue

                        building_id = c.get_tile_building_id(cur)
                        e_type = c.get_entity_type(building_id)
                        if c.get_team(building_id) == my_team or e_type == EntityType.MARKER:
                            if building_id is None or e_type in C.UNIMPORTANT:
                                if c.get_action_cooldown() or c.get_global_resources()[0] < c.get_barrier_cost()[0]:
                                    return False
                                if c.get_tile_builder_bot_id(cur) is not None:
                                    return False
                                if cur.distance_squared(my_pos) > 2:
                                    return False
                                if c.can_destroy(cur):
                                    c.destroy(cur)
                                c.build_barrier(cur)
                                movement.act(c)
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
                                movement.act(c)
                            return False

            return True

        if not on_ore:
            dist = my_pos.distance_squared(self.path[0])
            if dist <= 13:
                building_id = c.get_tile_building_id(self.path[0])
                e_type: EntityType = c.get_entity_type(building_id)
                if e_type != EntityType.HARVESTER:
                    if dist == 1:
                        if c.get_team(c.get_tile_building_id(my_pos)) != my_team and not enemy_near:
                            if c.can_fire(my_pos):
                                c.fire(my_pos)
                            return

                    if dist <= 2:
                        if c.get_action_cooldown():
                            return

                        d: Direction = my_pos.direction_to(self.path[0])
                        if not c.get_move_cooldown() and (c.can_move(d) or c.get_global_resources()[0] >= c.get_road_cost()[0]):
                            bb_id = c.get_tile_builder_bot_id(self.path[0])
                            if bb_id is None:
                                if c.get_entity_type(building_id) != EntityType.ROAD:
                                    if c.can_destroy(self.path[0]):
                                        c.destroy(self.path[0])
                                movement.enrich(c)
                                movement.move(d)
                                on_ore = True
                            else:
                                return
                        else:
                            return
                    else:
                        self.nav.move(c, self.path[0], movement)
                        return

        do_build: bool = False
        if on_ore:
            pos: Position = self.path[1]
            do_build = True
            building_id = c.get_tile_building_id(my_pos)
            e_type: EntityType = c.get_entity_type(building_id)
            if e_type == EntityType.ROAD and c.get_team(building_id) != my_team:
                if c.can_fire(my_pos):
                    c.fire(my_pos)

            if not build_barriers():
                return

            building_id = c.get_tile_building_id(pos)
            if self.mode == 2 and len(self.path) == 3:
                # Special case bruh
                if building_id is None:
                    if c.can_build_road(pos):
                        c.build_road(pos)
                    return

                if U.can_afford("harvester"):
                    d: Direction = my_pos.direction_to(pos)
                    if c.can_move(d):
                        movement.move(d)

                        if c.can_destroy(self.path[0]):
                            c.destroy(self.path[0])

                        c.build_harvester(self.path[0])
                return
            else:
                if c.get_team(building_id) == my_team:
                    if (e_type := c.get_entity_type(building_id)) in C.CONVEYOR_VARIANT or e_type == EntityType.GUNNER:
                        if not c.get_action_cooldown():
                            d: Direction = my_pos.direction_to(pos)
                            if not c.can_move(d):
                                options: list[Direction] = []
                                for d in C.DIRECTIONS:
                                    if c.can_move(d):
                                        options.append(d)

                                if options:
                                    d = random.choice(options)
                                else:
                                    return

                            if c.get_global_resources()[0] >= c.get_harvester_cost()[0]:
                                movement.move(d)
                                if c.can_destroy(self.path[0]):
                                    c.destroy(self.path[0])

                                c.build_harvester(self.path[0])
                        return

        if my_pos.distance_squared(self.path[0]) <= 13:
            mine: list[bool] = [False] * 4
            enemy: list[bool] = [False] * 4
            turret: list[bool] = [False] * 4
            for i in range(4):
                d: Direction = C.CARDINAL[i]
                cur = self.path[0].add(d)
                if not U.on_the_map(cur) or c.get_tile_env(cur) == Environment.WALL:
                    continue
                building_id = c.get_tile_building_id(cur)
                e_type = c.get_entity_type(building_id)
                if c.get_team(building_id) == my_team or e_type == EntityType.MARKER:
                    bb_id = c.get_tile_builder_bot_id(cur)
                    mine[i] = bb_id is None or bb_id == my_id
                else:
                    enemy[i] = True
                    turret[i] = e_type in C.TURRET

            for i in range(4):
                if turret[i]:
                    if mine[i - 1]:
                        # building_id = c.get_tile_building_id(self.path[0].add(C.CARDINAL[i]))
                        # d: Direction = self.path[0].add(C.CARDINAL[i]).direction_to(self.path[0].add(C.CARDINAL[i - 1]))
                        # if abs()
                        j = i - 1
                    elif mine[i + 1]:
                        j = (i + 1) % 4
                    else:
                        continue

                    cur = self.path[0].add(C.CARDINAL[j])
                    building_id = c.get_tile_building_id(cur)
                    d: Direction = cur.direction_to(self.path[0].add(C.CARDINAL[i]))
                    if building_id is not None and c.get_entity_type(building_id) == EntityType.GUNNER:
                        if c.get_direction(building_id) == d:
                            continue

                    dist = my_pos.distance_squared(cur)
                    if not dist:
                        for d in C.DIRECTIONS:
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

        if self.index == len(self.path) - 1:
            # Special case where ore is adjacent to conveyor
            if len(self.path) == 2:
                dist = my_pos.distance_squared(self.path[0])
                if dist == 0:
                    if c.get_global_resources()[0] >= c.get_harvester_cost()[0]:
                        if not c.get_move_cooldown() and not c.get_action_cooldown():
                            for d in C.DIRECTIONS:
                                if c.can_move(d):
                                    movement.move(d)

                                    if c.can_destroy(my_pos):
                                        c.destroy(my_pos)
                                    if c.can_build_harvester(my_pos):
                                        c.build_harvester(my_pos)
                                        self.done = True

                                    return

                            for d in C.DIRECTIONS:
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
            for _ in range(3 if di in C.CARDINAL else 2):
                cur = cur.add(di)
                if U.is_visible(cur):
                    if c.get_tile_env(cur) == Environment.WALL:
                        break
                    else:
                        b_id = c.get_tile_building_id(cur)
                        if b_id is not None:
                            e_type = c.get_entity_type(b_id)
                            if c.get_team(b_id) == my_team:
                                if e_type in C.UNIMPORTANT:
                                    continue
                            else:
                                if e_type == EntityType.MARKER:
                                    continue
                                else:
                                    keep_gunner = True
                            break
                else:
                    break

            if keep_gunner:
                if my_pos != self.path[self.index - 1]:
                    movement.enrich(c)
                    self.nav.move(c, self.path[self.index - 1], movement)

                    if not c.get_move_cooldown():
                        if my_pos == pos.add(c.get_direction(building_id)):
                            options: list[Direction] = []
                            for d in C.DIRECTIONS:
                                if movement.can_move(d):
                                    options.append(d)
                            if options:
                                movement.move(random.choice(options))
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
        has_enemy = c.get_team(c.get_tile_builder_bot_id(pos)) != my_team
        if c.get_team(building_id) != my_team and e_type != EntityType.MARKER:
            if e_type in C.DESTROY_ENEMY and not has_enemy:
                if my_pos != pos:
                    self.nav.move(c, pos, movement)
                if c.can_fire(pos):
                    c.fire(pos)
                return
            else:
                need_gunner = True
        else:
            need_gunner = False

        if need_gunner:
            if self.mode == 2:
                self.index = 0
                return

            self.index -= 1
            if not self.index:
                return
            pos = self.path[self.index]
        else:
            nxt = self.path[self.index + 1]
            need_gunner = c.is_in_vision(nxt)
            if need_gunner:
                building_id = c.get_tile_building_id(nxt)
                e_type = c.get_entity_type(building_id)
                need_gunner &= c.get_team(building_id) != my_team and e_type not in C.DESTROY_ENEMY and e_type != EntityType.MARKER
        nxt = self.path[self.index + 1]

        dist = my_pos.distance_squared(pos)
        if dist <= 2:
            if self.mode == 2 and self.index == len(self.path) - 2:
                # TODO: what if conveyor is gone bruh
                if self.splitter is None:
                    # TODO: fix
                    for d in C.CARDINAL:
                        cur: Position = pos.add(d)
                        if U.on_the_map(cur):
                            building_id: int = c.get_tile_building_id(cur)
                            if c.get_entity_type(building_id) in C.MONOCHILD_CONVEYOR:
                                if cur.add(c.get_direction(building_id)) != pos:
                                    self.splitter = cur

                if c.get_entity_type(c.get_tile_building_id(self.splitter)) == EntityType.SPLITTER:
                    if self.conveyor is None:
                        can_replace = C.UNIMPORTANT | {EntityType.BARRIER}
                        for d in C.CARDINAL:
                            cur: Position = pos.add(d)
                            if cur != self.splitter and U.on_the_map(cur) and c.get_tile_env(cur) == Environment.EMPTY:
                                building_id: int = c.get_tile_building_id(cur)
                                if c.get_team(building_id) == my_team:
                                    if building_id is None or (e_type := c.get_entity_type(building_id)) in can_replace:
                                        self.conveyor = cur  # TODO: ?
                                        break
                                    elif e_type in C.CONVEYOR:
                                        if c.get_direction(building_id) != d.opposite():
                                            self.conveyor = cur
                                    elif e_type == EntityType.BRIDGE:
                                        if c.get_bridge_target(building_id) != pos:
                                            self.conveyor = cur
                                else:
                                    if c.get_entity_type(building_id) in C.UNIMPORTANT:
                                        self.conveyor = cur
                                        break

                        print(self.conveyor)
                        if self.conveyor is None:
                            return  # BRUH

                    if c.get_entity_type(c.get_tile_building_id(self.conveyor)) in C.MONOCHILD_CONVEYOR:
                        if c.get_entity_type(c.get_tile_building_id(pos)) == EntityType.FOUNDRY:
                            self.done = True
                        else:
                            rich: bool = c.get_global_resources()[0] >= c.get_foundry_cost()[0]
                            if not dist and rich:
                                for d in C.DIRECTIONS:
                                    if c.can_move(d):
                                        c.move(d)
                                        dist = c.get_position().direction_to(pos)
                                        break

                            if dist:
                                if rich:
                                    if c.can_destroy(pos):
                                        c.destroy(pos)
                                    if c.can_build_foundry(pos):
                                        c.build_foundry(pos)
                                    else:
                                        pass  # TODO
                                else:
                                    movement.enrich(c)
                                    self.nav.move(c, pos, movement)
                    else:
                        building_id = c.get_tile_building_id(self.conveyor)
                        if c.get_team(building_id) == my_team or c.get_entity_type(building_id) == EntityType.MARKER:
                            if dist:
                                movement.enrich(c)
                                self.nav.move(c, pos, movement)

                            target: Position | None = None
                            d: Direction = c.get_direction(c.get_tile_building_id(self.splitter)).opposite()
                            for e in C.CARDINAL:
                                if e != d:
                                    cur: Position = self.splitter.add(e)
                                    if U.on_the_map(cur):
                                        if c.get_entity_type(c.get_tile_building_id(cur)) in C.CONVEYOR_VARIANT:
                                            if self.conveyor.distance_squared(cur) == 1 or target is None:
                                                target = cur

                            if target is None:
                                return  # BRUH
                            else:
                                if self.conveyor.distance_squared(target) == 1:
                                    if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_conveyor_cost()[0]:
                                        if c.get_position().distance_squared(self.conveyor) <= 2:
                                            d: Direction = self.conveyor.direction_to(target)
                                            if c.can_destroy(self.conveyor):
                                                c.destroy(self.conveyor)
                                            if c.can_build_conveyor(self.conveyor, d):
                                                c.build_conveyor(self.conveyor, d)
                                            else:
                                                pass  # TODO
                                else:
                                    if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_bridge_cost()[0]:
                                        if c.get_position().distance_squared(self.conveyor) <= 2:
                                            if c.can_destroy(self.conveyor):
                                                c.destroy(self.conveyor)
                                            if c.can_build_bridge(self.conveyor, target):
                                                c.build_bridge(self.conveyor, target)
                                            else:
                                                pass  # TODO
                        else:
                            if my_pos != self.conveyor:
                                movement.enrich(c)
                                self.nav.move(c, self.conveyor, movement)
                                my_pos = c.get_position()

                            if my_pos == self.conveyor:
                                if c.can_fire(my_pos):
                                    c.fire(my_pos)
                else:
                    if dist:
                        movement.enrich(c)
                        self.nav.move(c, pos, movement)

                    if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_splitter_cost()[0]:
                        if c.get_position().distance_squared(self.splitter) <= 2:
                            for d in C.CARDINAL:
                                cur = self.splitter.add(d.opposite())
                                if U.on_the_map(cur):
                                    building_id = c.get_tile_building_id(cur)
                                    e_type = c.get_entity_type(building_id)
                                    if e_type in C.CONVEYOR:
                                        if c.get_direction(building_id) == d:
                                            break
                                    elif e_type == EntityType.HARVESTER:
                                        break
                                    elif e_type == EntityType.BRIDGE:
                                        if c.get_bridge_target(building_id) == self.splitter:
                                            break

                            if c.can_destroy(self.splitter):
                                c.destroy(self.splitter)
                            if c.can_build_splitter(self.splitter, d):
                                c.build_splitter(self.splitter, d)
                            else:
                                pass  # TODO
            else:
                d: Direction = pos.direction_to(nxt)

                enemy_core = tile_manager.enemy_core
                if enemy_core is not None:
                    if pos.distance_squared(enemy_core) <= 18:
                        # Attack!
                        need_gunner = True
                        d = pos.direction_to(enemy_core)

                if need_gunner:
                    pass_: int = tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy
                    e: Direction = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
                    if e is None:
                        movement.enrich(c)
                        if movement.is_rich:
                            e: Direction = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, (tile_manager.pass_ | tile_manager.buildable) & ~tile_manager.ally & ~tile_manager.enemy)

                    if e is not None and e != Direction.CENTRE:
                        movement.move(e)

                    if c.can_destroy(pos):
                        c.destroy(pos)

                    if U.can_afford("gunner"):
                        if c.can_build_gunner(pos, d):
                            c.build_gunner(pos, d)
                else:
                    if not c.get_move_cooldown() and not c.get_action_cooldown():
                        dist = pos.distance_squared(self.home)
                        if c.get_current_round() >= 100 and (dist == 13 or dist == 18):
                            d: Direction = self.home.direction_to(pos)
                            if dist == 17:
                                dx, dy = d.delta()
                                target: Position = Position(pos.x - dx * 3, pos.y - dy * 3)
                            else:
                                target: Position = self.home.add(d)

                            if c.get_global_resources()[0] >= c.get_bridge_cost()[0]:
                                if c.can_destroy(pos):
                                    c.destroy(pos)

                                c.build_bridge(pos, target)
                                self.index = len(self.path) - 1
                        else:
                            dx, dy = d.delta()

                            def is_clear(cur: Position):
                                if c.get_tile_env(cur) == Environment.EMPTY:
                                    building_id = c.get_tile_building_id(cur)
                                    if c.get_team(building_id) == my_team:
                                        if building_id is None or (e_type := c.get_entity_type(building_id)) in C.UNIMPORTANT or e_type == EntityType.BARRIER:
                                            self.path.insert(self.index + 1, cur)
                                            return True
                                    else:
                                        if (e_type := c.get_entity_type(building_id)) in C.DESTROY_ENEMY or e_type == EntityType.MARKER:
                                            self.path.insert(self.index + 1, cur)
                                            return True
                                return False

                            if dx and dy:
                                if is_clear(Position(pos.x + dx, pos.y)):
                                    dy = 0
                                    d = C.DIRECTION_MAP[(dx, 0)]
                                elif is_clear(Position(pos.x, pos.y + dy)):
                                    dx = 0
                                    d = C.DIRECTION_MAP[(0, dy)]
                                else:
                                    if c.get_global_resources()[0] >= c.get_bridge_cost()[0]:
                                        if c.can_destroy(pos):
                                            c.destroy(pos)

                                        c.build_bridge(pos, nxt)
                                        self.index += 1

                            if not dx or not dy:
                                if c.get_global_resources()[0] >= c.get_conveyor_cost()[0]:
                                    if c.can_destroy(pos):
                                        c.destroy(pos)

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
        elif not c.get_move_cooldown():
            # TODO: destroy launchers
            if do_build:
                return

            pass_: int = tile_manager.pass_ & ~tile_manager.ally & ~tile_manager.enemy
            d: Direction = bfs.bfs_to_pos(pos.x - my_pos.x, pos.y - my_pos.y, pass_)
            if d is None or d != Direction.CENTRE and not c.can_move(d):
                d = bfs.bfs_adj_exc(pos.x - my_pos.x, pos.y - my_pos.y, pass_)

            if d is not None and d != Direction.CENTRE:
                movement.move(d)
