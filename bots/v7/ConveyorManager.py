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
        self.mode: int = 0  # 0: avoid joining, 1: normal, 2: axionite, 3: destroy enemy
        self.path_index: list[list[bool]] | None = None
        self.path = []
        self.index = 1
        self.done: bool = False
        self.nav: Nav = nav
        self.home: Position = home
        self.splitter: Position | None = None
        self.conveyor: Position | None = None
        self.prev_resource: int | None = None

    @staticmethod
    def scaling(path: list[Position]):
        scaling: int = 0
        prev: Position = path[0]
        for pos in path[1:]:
            if prev.distance_squared(pos) == 1:
                scaling += 1
            else:
                scaling += 10
            prev = pos
        return scaling

    def compute(self, c: Controller, tile_manager: TileManager, start: Position, avoid_joining: bool, is_harvester: bool = True):
        W_plus_1 = C.W + 1
        pass_: int = tile_manager.reach
        if avoid_joining:
            pass_ &= ~tile_manager["conveyor"]
        else:
            self.mode = 1

        x, y = start
        bit: int = 1 << (y * W_plus_1 + x)
        if is_harvester:
            adj: int = bit << 1 | bit >> 1 | bit << W_plus_1 | bit >> W_plus_1
        else:
            adj: int = bit

        x, y = self.home
        cur: int = 1 << (y * W_plus_1 + x)
        cur |= cur << 1 | cur >> 1
        cur |= cur << W_plus_1 | cur >> W_plus_1

        if cur & adj:
            return [start, start.add(start.direction_to(self.home))]

        seen: list[int] = [cur]
        map_mask: int = C.MAP_MASK
        while len(seen) < 100:
            cur: int = seen[-1]
            cur |= cur << 1 | cur >> 1 | cur << W_plus_1 | cur >> W_plus_1

            if len(seen) >= 2:
                prev: int = seen[-2]
                prev |= prev << 1 | prev >> 1
                cur |= prev << W_plus_1 | prev >> W_plus_1
                if len(seen) >= 6:
                    prev: int = seen[-6]
                    prev |= prev << 1 | prev >> 1
                    prev |= prev << W_plus_1 | prev >> W_plus_1
                    prev &= map_mask
                    prev |= prev << 1 | prev >> 1
                    cur |= prev << W_plus_1 | prev >> W_plus_1

            cur &= pass_

            if cur & adj:
                path: list[Position] = [start]
                if is_harvester:
                    seen.append(cur)
                i: int = len(seen)
                while i:
                    cur: int = seen[i - 1]
                    if bit >> W_plus_1 & cur:
                        start = start.add(Direction.NORTH)
                        bit >>= W_plus_1
                        i -= 1
                    elif bit << 1 & cur:
                        start = start.add(Direction.EAST)
                        bit <<= 1
                        i -= 1
                    elif bit << W_plus_1 & cur:
                        start = start.add(Direction.SOUTH)
                        bit <<= W_plus_1
                        i -= 1
                    elif bit >> 1 & cur:
                        start = start.add(Direction.WEST)
                        bit >>= 1
                        i -= 1
                    else:
                        cur: int = seen[i - 2]
                        if bit >> (W_plus_1 - 1) & cur:
                            start = start.add(Direction.NORTHEAST)
                            bit >>= W_plus_1 - 1
                            i -= 2
                        elif bit << (W_plus_1 + 1) & cur:
                            start = start.add(Direction.SOUTHEAST)
                            bit <<= W_plus_1 + 1
                            i -= 2
                        elif bit << (W_plus_1 - 1) & cur:
                            start = start.add(Direction.SOUTHWEST)
                            bit <<= W_plus_1 - 1
                            i -= 2
                        elif bit >> (W_plus_1 + 1) & cur:
                            start = start.add(Direction.NORTHWEST)
                            bit >>= W_plus_1 + 1
                            i -= 2
                        else:
                            cur: int = seen[i - 6]
                            mask = bit | bit << 1 | bit >> 1
                            mask |= mask << W_plus_1 | mask >> W_plus_1
                            mask &= map_mask
                            mask |= mask << 1 | mask >> 1
                            mask |= mask << W_plus_1 | mask >> W_plus_1
                            index: int = (mask & cur).bit_length() - 1
                            start = Position(index % W_plus_1, index // W_plus_1)
                            bit = 1 << index
                            i -= 6
                    path.append(start)
                return path

            seen.append(cur)

        return []

    def compute_to_conveyors(self, tile_manager: TileManager, start: Position) -> list[Position]:
        W_plus_1: int = C.W + 1
        pass_: int = tile_manager.reach

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

        pass_ &= ~seen[0]

        while len(seen) < 100:
            cur: int = seen[-1]
            cur |= cur << 1 | cur >> 1 | cur << W_plus_1 | cur >> W_plus_1

            if len(seen) >= 3:
                prev: int = seen[-2]
                prev |= prev << 1 | prev >> 1
                cur |= prev | prev << W_plus_1 | prev >> W_plus_1
            elif len(seen) == 1:
                cur &= ~too_walled

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

    def compute_to_enemy(self, tile_manager: TileManager) -> list[Position]:
        W_plus_1: int = C.W + 1

        my_ores: int = sum(
            1 << (y * W_plus_1 + x) for x, y in tile_manager.my_ores
        )
        enemy_ores: int = sum(
            1 << (y * W_plus_1 + x) for x, y in tile_manager.enemy_ores
        )

        if not my_ores or not enemy_ores:
            return []

        conveyor: int = tile_manager["conveyor"]
        pass_: int = tile_manager.reach & ~conveyor

        target: int = (my_ores << 1 | my_ores >> 1 | my_ores << W_plus_1 | my_ores >> W_plus_1) & pass_
        seen: list[int] = [enemy_ores]

        for i in range(100):
            cur: int = seen[-1]
            cur |= cur << 1 | cur >> 1 | cur << W_plus_1 | cur >> W_plus_1

            if i >= 2:
                prev: int = seen[-2]
                prev |= prev << 1 | prev >> 1
                cur |= prev | prev << W_plus_1 | prev >> W_plus_1

            cur &= pass_
            seen.append(cur)

            if cur & target:
                index: int = ((cur << 1 | cur >> 1 | cur << W_plus_1 | cur >> W_plus_1) & my_ores).bit_length() - 1
                path: list[Position] = [Position(index % W_plus_1, index // W_plus_1)]
                i: int = len(seen)
                while i:
                    bit = 1 << index
                    intersection: int = (bit << 1 | bit >> 1 | bit << W_plus_1 | bit >> W_plus_1) & seen[i - 1]
                    if intersection:
                        index: int = intersection.bit_length() - 1
                        path.append(Position(index % W_plus_1, index // W_plus_1))
                        i -= 1
                    else:
                        bit |= bit << 1 | bit >> 1
                        bit |= bit << W_plus_1 | bit >> W_plus_1
                        intersection: int = bit & seen[i - 2]
                        # Must have
                        index: int = intersection.bit_length() - 1
                        path.append(Position(index % W_plus_1, index // W_plus_1))
                        i -= 2
                return path

        return []

    def generate_path(self, c: Controller, tile_manager: TileManager, start: Position, mode: int = 0):
        if mode <= 1:
            path = self.compute(c, tile_manager, start, not mode)
        elif mode == 2:
            path = self.compute_to_conveyors(tile_manager, start)
            self.mode = 2
        else:
            path = self.compute_to_enemy(tile_manager)
            self.mode = 3
        if path:
            self.path = path
            self.index_path()

            for i in range(1, len(path)):
                c.draw_indicator_line(path[i - 1], path[i], 255, 0, 255)
            # if self.mode == 3:
            #     c.resign()

    def index_path(self):
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
                if ConveyorManager.scaling(path) < ConveyorManager.scaling(self.path[self.index:]) or stuck:
                    self.path = self.path[:self.index] + path
                    self.index_path()
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
            if len(suffix) < len(self.path) - self.index:
                while self.path[self.index] != suffix[0]:
                    self.index -= 1
                self.path = self.path[:self.index]

                self.path += suffix

                for i in range(1, len(self.path)):
                    c.draw_indicator_line(self.path[i - 1], self.path[i], 255, 255, 0)

                self.index_path()

    def update(self, c: Controller, movement: Movement, tile_manager: TileManager, nav: Nav, repair: bool = False):
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
        movement.enrich(c)

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
                                nav.move(c, cur, movement)
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
                        if not c.get_move_cooldown() and (c.can_move(d) or U.can_afford("road")):
                            bb_id = c.get_tile_builder_bot_id(self.path[0])
                            if bb_id is None:
                                if c.get_entity_type(building_id) != EntityType.ROAD:
                                    if c.can_destroy(self.path[0]):
                                        c.destroy(self.path[0])
                                        c.build_road(self.path[0])
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
                    elif mine[(i + 1) % 4]:
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
            elif self.mode == 3:
                end: Position = self.path[-1]
                if c.is_in_vision(end):
                    building_id = c.get_tile_building_id(end)
                    if c.get_entity_type(building_id) == EntityType.BARRIER and c.get_team(building_id) == my_team:
                        self.done = True
                        return

                if U.can_afford("barrier"):
                    self.nav.move(c, end, movement, adj=True, exc=True)
                else:
                    self.nav.move(c, end, movement)

                # TODO: fire
                if c.can_build_barrier(end):
                    c.build_barrier(end)
                    self.done = True
            else:
                self.done = not on_ore
            return

        pos: Position = self.path[self.index]
        if not c.is_in_vision(pos):
            self.nav.move(c, pos, movement)
            return

        building_id = c.get_tile_building_id(pos)
        e_type: EntityType = c.get_entity_type(building_id)
        if e_type in C.TURRET and c.get_team(building_id) == my_team:
            if e_type == EntityType.GUNNER:
                keep_turret: bool = False
                di: Direction = c.get_direction(building_id)
                for d in C.DIRECTIONS:
                    cur: Position = pos.add(d)
                    if c.is_in_vision(cur):
                        b_id = c.get_tile_building_id(cur)
                        if c.get_team(b_id) != my_team and c.get_entity_type(b_id) not in C.UNIMPORTANT:
                            keep_turret = True
                            break
                else:
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
                                            keep_turret = True
                                    break
                        else:
                            break
            else:
                cur: Position = self.path[self.index - 1]
                building_id = c.get_tile_building_id(cur)
                resource: int | None = c.get_stored_resource_id(building_id)
                if resource == self.prev_resource and resource is not None:
                    keep_turret: bool = False
                else:
                    keep_turret: bool = True
                    self.prev_resource = resource

            if keep_turret:
                if my_pos != self.path[self.index - 1]:
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
                if self.mode == 3:
                    if c.can_build_barrier(self.path[-1]):
                        c.build_barrier(self.path[-1])

                if c.can_destroy(pos):
                    c.destroy(pos)
                else:
                    nav.move(c, pos, movement)

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
            nxt: Position = self.path[self.index + 1]
            need_gunner = c.is_in_vision(nxt)
            if need_gunner:
                building_id = c.get_tile_building_id(nxt)
                e_type = c.get_entity_type(building_id)
                need_gunner &= c.get_team(building_id) != my_team and e_type not in C.DESTROY_ENEMY and e_type != EntityType.MARKER
        nxt = self.path[self.index + 1]

        if self.mode == 3 and self.index == len(self.path) - 2:
            for d in C.CARDINAL:
                cur: Position = nxt.add(d)
                if U.is_visible(cur):
                    b_id = c.get_tile_building_id(cur)
                    if c.get_team(b_id) != my_team and c.get_entity_type(b_id) not in C.UNIMPORTANT:
                        need_gunner = True
                        break

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
                                    self.nav.move(c, pos, movement)
                    else:
                        building_id = c.get_tile_building_id(self.conveyor)
                        if c.get_team(building_id) == my_team or c.get_entity_type(building_id) == EntityType.MARKER:
                            if dist:
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
                                self.nav.move(c, self.conveyor, movement)
                                my_pos = c.get_position()

                            if my_pos == self.conveyor:
                                if c.can_fire(my_pos):
                                    c.fire(my_pos)
                else:
                    if dist:
                        self.nav.move(c, pos, movement)

                    if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_splitter_cost()[0]:
                        if c.get_position().distance_squared(self.splitter) <= 2:
                            candidate: Direction | None = None
                            for d in C.CARDINAL:
                                cur = self.splitter.add(d.opposite())
                                if U.on_the_map(cur):
                                    if cur == pos:
                                        continue
                                    building_id = c.get_tile_building_id(cur)
                                    e_type = c.get_entity_type(building_id)
                                    if e_type in C.CONVEYOR:
                                        if c.get_direction(building_id) == d:
                                            break
                                        continue
                                    elif e_type == EntityType.HARVESTER:
                                        break
                                    candidate = d
                            else:
                                # TODO: what if None
                                d = candidate

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
                    nav.move(c, pos, movement, adj=True, exc=True)

                    if U.can_afford("gunner"):
                        if c.can_destroy(pos):
                            c.destroy(pos)

                        if c.can_build_gunner(pos, d):
                            c.build_gunner(pos, d)
                else:
                    # Try build sentinel
                    # TODO: refine
                    best_dir: Direction | None = None
                    # if self.index >= 2 and self.mode <= 1:
                    #     target: set[EntityType] = C.CONVEYOR_VARIANT | {EntityType.BARRIER, EntityType.HARVESTER}
                    #     max_count: int = 0
                    #     e: Direction = self.path[self.index - 1].direction_to(pos)
                    #     for e in (e.rotate_left().rotate_left(), e.rotate_left(), e, e.rotate_right(), e.rotate_right().rotate_right()):
                    #         count: int = 0
                    #         for cur in c.get_attackable_tiles_from(pos, e, EntityType.SENTINEL):
                    #             if c.is_in_vision(cur):
                    #                 building_id = c.get_tile_building_id(cur)
                    #                 if c.get_team(building_id) != my_team:
                    #                     if c.get_entity_type(building_id) in target:
                    #                         count += 1
                    #         if count > max_count:
                    #             best_dir = e
                    #             max_count = count

                    if best_dir is not None:
                        nav.move(c, pos, movement, adj=True, exc=True)

                        if U.can_afford("sentinel"):
                            if c.can_destroy(pos):
                                c.destroy(pos)

                            if c.can_build_sentinel(pos, best_dir):
                                c.build_sentinel(pos, best_dir)
                                cur: Position = self.path[self.index - 1]
                                building_id = c.get_tile_building_id(cur)
                                self.prev_resource = c.get_stored_resource_id(building_id)
                    else:
                        if not c.get_move_cooldown() and not c.get_action_cooldown():
                            if pos.distance_squared(nxt) == 2:
                                dx, dy = d.delta()

                                def is_clear(cur: Position):
                                    if c.get_tile_env(cur) == Environment.EMPTY:
                                        building_id = c.get_tile_building_id(cur)
                                        nonlocal nxt
                                        if c.get_team(building_id) == my_team:
                                            if building_id is None or (e_type := c.get_entity_type(building_id)) in C.UNIMPORTANT or e_type == EntityType.BARRIER:
                                                self.path.insert(self.index + 1, nxt := cur)
                                                return True
                                        else:
                                            if (e_type := c.get_entity_type(building_id)) in C.DESTROY_ENEMY or e_type == EntityType.MARKER:
                                                self.path.insert(self.index + 1, nxt := cur)
                                                return True
                                    return False

                                if is_clear(Position(pos.x + dx, pos.y)) or is_clear(Position(pos.x, pos.y + dy)):
                                    d = pos.direction_to(nxt)

                            if pos.distance_squared(nxt) == 1:
                                if c.get_global_resources()[0] >= c.get_conveyor_cost()[0]:
                                    if c.can_destroy(pos):
                                        c.destroy(pos)

                                    c.build_conveyor(pos, d)
                                    self.index += 1
                            else:
                                if c.get_global_resources()[0] >= c.get_bridge_cost()[0]:
                                    if self.mode <= 2:
                                        while self.index + 2 < len(self.path) and self.path[self.index + 2].distance_squared(pos) <= 9:
                                            self.path.pop(self.index + 1)
                                            nxt = self.path[self.index + 1]

                                    if c.can_destroy(pos):
                                        c.destroy(pos)

                                    c.build_bridge(pos, nxt)
                                    self.index += 1

                                    self.index_path()

                            if do_build:
                                return

                            nav.move(c, pos, movement)
        elif not c.get_move_cooldown():
            # TODO: destroy launchers
            if do_build:
                return

            nav.move(c, pos, movement)
