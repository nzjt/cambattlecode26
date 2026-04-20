from cambc import *
import consts as C
import utils as U
from Wander import Wander
from Network import Network


class TileManager:
    def __init__(self, home: Position):
        W, H = C.W, C.H
        self.home: Position = home
        self.pass_bitset: list[int] = [0] * H
        self.buildable_bitset: list[int] = [(1 << W) - 1] * H
        self.empty_bitset: list[int] = [0] * H
        self.titanium_bitset: list[int] = [0] * H
        self.conveyor_bitset: list[int] = [0] * H
        self.bridge_bitset: list[int] = [0] * H
        self.enemy_bitset: list[int] = [0] * H
        self.unit_bitset: list[int] = []
        self.build_harvester = [[True] * W for _ in range(H)]
        self.ban_harvester = [[False] * W for _ in range(H)]
        self.see_gun: bool = False
        self.bot_tracker: dict[int, tuple[Position, int, int]] = {}
        self.has_kill_chamber: bool = False
        self.axionite_ores: set[Position] = set()
        self.gunners: dict[Position, list] = {}
        self.gunner_covered_grid: list[list[bool]] = []
        self.gunner_covered: int = 0
        self.enemy_core: Position | None = None
        self.symmetry: int = 7
        self.my_ores: set[Position] = set()
        self.enemy_ores: set[Position] = set()
        self.to_heal: set[Position] = set()
        self.network: Network = Network(home)

        W_plus_1: int = W + 1
        mask: int = 0
        for row in (0x7c, 0xfe, 0x1ff, 0x1ff, 0x1ff, 0x1ff, 0x1ff, 0xfe, 0x7c):
            mask = mask << W_plus_1 | row
        self.vision_mask: int = mask
        self.seen: int = 0
        mask = 0x1ff
        for _ in range(H):
            mask |= mask << W_plus_1
        self.left: int = mask
        self.right: int = C.MAP_MASK & ~mask

        x, y = home
        self.reach: int = 1 << (y * (W + 1) + x)

        self.is_protection: dict[Position, Position] = {}
        self.lack_protection: dict[Position, Position] = {}
        self.empty_ore: set[Position] = set()
        self.unharvested: set[Position] = set()
        self.to_destroy: set[Position] = set()

        self.conveyor: int = 0
        self.bridge: int = 0
        self.enemy: int = 0

        self.recently_built: list[int] = []
        self.me_built: list[int] = []

        self.id_grid: list[list[int]] = [[0] * W for _ in range(H)]

    def allow(self, pos: Position):
        x, y = pos
        self.me_built[-1] |= 1 << (y * (C.W + 1) + x)

    def see(self, x: int, y: int):
        W_plus_1: int = C.W + 1
        mask: int = self.vision_mask
        if y >= 4:
            mask <<= (y - 4) * W_plus_1
        else:
            mask >>= (4 - y) * W_plus_1
        if x < 4:
            self.seen |= mask >> (4 - x) & self.left
        elif x + 4 < C.W:
            self.seen |= mask << (x - 4)
        else:
            self.seen |= mask << (x - 4) & self.right

    def sense(self, c: Controller, home: Position, wander: Wander):
        get_tile_building_id = c.get_tile_building_id
        get_tile_env = c.get_tile_env
        get_entity_type = c.get_entity_type
        get_tile_builder_bot_id = c.get_tile_builder_bot_id
        get_team = c.get_team
        get_direction = c.get_direction
        get_marker_value = c.get_marker_value

        my_id = c.get_id()
        my_pos: Position = c.get_position(my_id)
        my_team = get_team(my_id)

        self.see_gun = False
        for building_id in c.get_nearby_buildings(9):
            if c.get_entity_type(building_id) == EntityType.GUNNER and c.get_team(building_id) == my_team:
                self.see_gun = True

        W, H = C.W, C.H
        W_plus_1: int = W + 1
        pass_bitset: list[int] = self.pass_bitset
        buildable_bitset: list[int] = self.buildable_bitset
        empty_bitset: list[int] = self.empty_bitset
        titanium_bitset: list[int] = self.titanium_bitset
        conveyor_bitset: list[int] = self.conveyor_bitset
        bridge_bitset: list[int] = self.bridge_bitset
        enemy_bitset: list[int] = self.enemy_bitset
        unit_bitset = self.unit_bitset = [0] * H

        x, y = my_pos
        if x >= 4:
            shift = x - 4
            for mask, yi in [(0x7c, y - 4), (0xfe, y - 3), (0x1ff, y - 2), (0x1ff, y - 1), (0x1ff, y), (0x1ff, y + 1), (0x1ff, y + 2), (0xfe, y + 3), (0x7c, y + 4)]:
                if 0 <= yi < H:
                    mask = ~(mask << shift)
                    pass_bitset[yi] &= mask
                    buildable_bitset[yi] &= mask
                    enemy_bitset[yi] &= mask
                    conveyor_bitset[yi] &= mask
                    bridge_bitset[yi] &= mask
        else:
            shift = 4 - x
            for mask, yi in [(0x7c, y - 4), (0xfe, y - 3), (0x1ff, y - 2), (0x1ff, y - 1), (0x1ff, y), (0x1ff, y + 1), (0x1ff, y + 2), (0xfe, y + 3), (0x7c, y + 4)]:
                if 0 <= yi < H:
                    mask = ~(mask >> shift)
                    pass_bitset[yi] &= mask
                    buildable_bitset[yi] &= mask
                    enemy_bitset[yi] &= mask
                    conveyor_bitset[yi] &= mask
                    bridge_bitset[yi] &= mask

        ally, enemy = 0, 0
        ROAD = EntityType.ROAD
        BARRIER = EntityType.BARRIER
        MARKER = EntityType.MARKER
        CORE = EntityType.CORE
        GUNNER = EntityType.GUNNER
        CONVEYOR_VARIANT = C.CONVEYOR_VARIANT
        DIRECTED_CONVEYOR = C.DIRECTED_CONVEYOR

        bot_tracker = self.bot_tracker
        round = c.get_current_round()

        wander_seen: int = wander.seen

        gunners: dict[Position, list] = self.gunners

        symmetry: int = self.symmetry

        my_ores: set[Position] = self.my_ores
        enemy_ores: set[Position] = self.enemy_ores

        to_heal: set[Position] = {pos for pos in self.to_heal if not c.is_in_vision(pos) or c.get_hp(building_id := c.get_tile_building_id(pos)) < c.get_max_hp(building_id)}

        nxt: list[int] = self.network.nxt
        adj: list[list[int]] = self.network.adj

        is_protection: dict[Position, Position] = {
            pos: target for pos, target in self.is_protection.items() if not c.is_in_vision(pos) or (get_entity_type(building_id := get_tile_building_id(pos)) == EntityType.CONVEYOR and get_direction(building_id) == pos.direction_to(target) and get_team(building_id) == my_team)
        }
        lack_protection: dict[Position, Position] = {
            pos: target for pos, target in self.lack_protection.items() if not c.is_in_vision(pos) or (building_id := get_tile_building_id(pos)) is None or get_entity_type(building_id) in C.UNIMPORTANT or get_team(building_id) != my_team
        }
        empty_ore: set[Position] = self.empty_ore
        unharvested: set[Position] = self.unharvested

        raw_ores: list[Position] = []
        dangerous: list[Position] = []

        new_conveyor: int = 0

        id_grid: list[list[int]] = self.id_grid
        print(c.get_cpu_time_elapsed())
        for pos in c.get_nearby_tiles():
            xi, yi = pos

            building_id = get_tile_building_id(pos)
            env: Environment = get_tile_env(pos)
            index: int = yi * W + xi
            if building_id is None:
                bit: int = 1 << xi
                pass_bitset[yi] &= ~bit
                if env != Environment.WALL:
                    buildable_bitset[yi] |= bit
                else:
                    buildable_bitset[yi] &= ~bit
                j: int = nxt[index]
                if j >= 0:
                    adj[j].remove(index)
                    nxt[index] = -1
            else:
                e_type: EntityType = get_entity_type(building_id)
                team: Team = c.get_team(building_id)
                bit: int = 1 << xi
                if e_type == ROAD:
                    pass_bitset[yi] |= bit
                    j: int = nxt[index]
                    if j >= 0:
                        adj[j].remove(index)
                        nxt[index] = -1
                elif e_type in CONVEYOR_VARIANT:
                    pass_bitset[yi] |= bit
                    if team == my_team:
                        if c.get_hp(building_id) < 20:
                            to_heal.add(pos)
                        if e_type in DIRECTED_CONVEYOR:
                            d: Direction = get_direction(building_id)
                            conveyor_bitset[yi] |= bit
                            target = pos.add(d)
                        else:
                            target: Position = c.get_bridge_target(building_id)
                            bridge_bitset[yi] |= bit
                        j: int = nxt[index]
                        if j >= 0:
                            adj[j].remove(index)
                        xk, yk = target
                        k: int = yk * W + xk
                        nxt[index] = k
                        adj[k].append(index)
                        if my_pos.distance_squared(pos) <= 10:
                            bit: int = 1 << (index + yi)
                            wander_seen |= bit
                        if building_id != id_grid[yi][xi]:
                            new_conveyor |= 1 << (k + yk)
                    else:
                        enemy_bitset[yi] |= bit
                elif e_type == BARRIER:
                    pass_bitset[yi] &= ~bit
                    buildable_bitset[yi] &= ~bit
                    if team == my_team:
                        if c.get_hp(building_id) < 30:
                            to_heal.add(pos)
                    else:
                        enemy_bitset[yi] |= bit
                        dangerous.append(pos)
                    j: int = nxt[index]
                    if j >= 0:
                        adj[j].remove(index)
                        nxt[index] = -1
                elif e_type == CORE:
                    if team == my_team:
                        if c.get_hp(building_id) < 500:
                            to_heal.add(pos)
                        pass_bitset[yi] |= bit
                    else:
                        enemy_bitset[yi] |= bit
                        buildable_bitset[yi] &= ~bit
                        self.enemy_core = c.get_position(building_id)
                elif e_type == MARKER:
                    buildable_bitset[yi] |= bit
                    if self.enemy_core is None:
                        if team == my_team:
                            symmetry &= get_marker_value(building_id)
                    j: int = nxt[index]
                    if j >= 0:
                        adj[j].remove(index)
                        nxt[index] = -1
                elif e_type == GUNNER:
                    pass_bitset[yi] &= ~bit
                    buildable_bitset[yi] &= ~bit
                    if team == my_team:
                        if c.get_hp(building_id) < 40:
                            to_heal.add(pos)
                        if pos in gunners:
                            gunners[pos][0] = get_direction(building_id)
                        else:
                            gunners[pos] = [get_direction(building_id), False]
                        if pos.distance_squared(self.home) <= 8:
                            if pos.add(c.get_direction(building_id)).distance_squared(self.home) <= 8:
                                self.has_kill_chamber = True
                    else:
                        dangerous.append(pos)
                        enemy_bitset[yi] |= bit
                    j: int = nxt[index]
                    if j >= 0:
                        adj[j].remove(index)
                        nxt[index] = -1
                elif e_type == EntityType.SENTINEL:
                    if team != my_team:
                        dangerous.append(pos)
                        enemy_bitset[yi] |= bit
                    j: int = nxt[index]
                    if j >= 0:
                        adj[j].remove(index)
                        nxt[index] = -1
                else:
                    pass_bitset[yi] &= ~bit
                    buildable_bitset[yi] &= ~bit
                    if team == my_team:
                        if c.get_hp(building_id) < c.get_max_hp(building_id):
                            to_heal.add(pos)
                    else:
                        enemy_bitset[yi] |= bit
                    j: int = nxt[index]
                    if j >= 0:
                        adj[j].remove(index)
                        nxt[index] = -1
            if env == Environment.EMPTY:
                empty_bitset[yi] |= 1 << xi
            elif env != Environment.WALL:
                if env == Environment.ORE_TITANIUM:
                    titanium_bitset[yi] |= 1 << xi
                    if self.ban_harvester[yi][xi]:
                        self.build_harvester[yi][xi] = False
                        empty_ore.discard(pos)
                    else:
                        raw_ores.append(pos)
                        if get_entity_type(building_id) == EntityType.HARVESTER:
                            nxt[yi * W + xi] = -3
                else:
                    if self.ban_harvester[yi][xi]:
                        self.build_harvester[yi][xi] = False
                        self.axionite_ores.discard(pos)
                    elif building_id is not None and c.get_entity_type(building_id) == EntityType.HARVESTER:
                        self.build_harvester[yi][xi] = False
                        self.axionite_ores.discard(pos)
                    else:
                        self.axionite_ores.add(pos)

            bb_id = get_tile_builder_bot_id(pos)
            if bb_id is not None:
                unit_bitset[yi] |= 1 << xi
                team = c.get_team(bb_id)
                dx = xi - my_pos.x
                dy = yi - my_pos.y
                if team == my_team:
                    ally |= 1 << (dx + dy * 10 + 44)
                    self.see(xi, yi)
                else:
                    enemy |= 1 << (dx + dy * 10 + 44)
                if bb_id in bot_tracker and bot_tracker[bb_id][0] == pos and bot_tracker[bb_id][2] == round - 1:
                    lo = bot_tracker[bb_id][1]
                else:
                    lo = round
                bot_tracker[bb_id] = (pos, lo, round)
        print(c.get_cpu_time_elapsed())

        unit_bitset[y] &= ~(1 << x)

        self.conveyor = self["conveyor"]
        self.bridge = self["bridge"]
        self.enemy = self["enemy"]
        wander.seen = wander_seen

        self.network.update(c)

        self.recently_built.append(new_conveyor)
        self.me_built.append(0)

        for pos in raw_ores:
            x, y = pos
            for j in adj[y * W + x]:
                is_protection[Position(j % W, j // W)] = pos

        fed: set[Position] = set()
        for pos in raw_ores:
            t0 = c.get_cpu_time_elapsed()
            is_mine: bool = True
            has_space, has_conveyor = False, False
            empty_adj: set[Position] = set()
            for d in C.CARDINAL:
                cur: Position = pos.add(d)
                if U.is_visible(cur) and c.get_tile_env(cur) != Environment.WALL:
                    b_id = c.get_tile_building_id(cur)
                    if b_id is None:
                        has_space = True
                        empty_adj.add(cur)
                    else:
                        e_type = c.get_entity_type(b_id)
                        if c.get_team(b_id) == my_team:
                            e_type = c.get_entity_type(b_id)
                            if e_type == EntityType.BRIDGE:
                                if c.get_bridge_target(b_id) != pos:
                                    has_conveyor |= True
                                    fed.add(cur)
                            elif e_type in C.CONVEYOR_VARIANT:
                                if cur not in is_protection:
                                    has_conveyor |= True
                                    fed.add(cur)
                            elif e_type in C.UNIMPORTANT:
                                has_space = True
                                empty_adj.add(cur)
                        else:
                            if e_type in C.UNIMPORTANT:
                                empty_adj.add(cur)
                                has_space = True

            building_id = c.get_tile_building_id(pos)
            unharvested.discard(pos)
            if building_id is None or get_entity_type(building_id) != EntityType.HARVESTER:
                if has_conveyor:
                    unharvested.add(pos)
                else:
                    unharvested.discard(pos)
            else:
                unharvested.discard(pos)
                xi, yi = pos
                if get_team(building_id) != my_team:
                    is_mine = False
                self.build_harvester[yi][xi] = False
                if pos.distance_squared(home) > 5:
                    if not has_conveyor and has_space:
                        self.build_harvester[yi][xi] = True
                if is_mine and has_conveyor:
                    for cur in empty_adj:
                        lack_protection[cur] = pos

            if is_mine:
                my_ores.add(pos)
                enemy_ores.discard(pos)
            else:
                enemy_ores.add(pos)
                my_ores.discard(pos)

            for d in C.CARDINAL:
                cur: Position = pos.add(d)
                xi, yi = cur
                if 0 <= xi < W and 0 <= yi < H:
                    if nxt[yi * W + xi] >= 0:
                        empty_ore.discard(pos)
                        break
            else:
                empty_ore.add(pos)
                unharvested.discard(pos)
            print(pos, c.get_cpu_time_elapsed() - t0)

        print(c.get_cpu_time_elapsed())
        self.lack_protection = lack_protection
        self.is_protection = is_protection

        to_destroy = self.to_destroy = set()
        for pos in dangerous:
            x, y = pos
            for i in adj[y * W + x]:
                x, y = i % W, i // W
                source: Position = Position(x, y)
                if adj[i] or source in fed:
                    to_destroy.add(source)

        self.gunners = {
            k: v for k, v in gunners.items() if not c.is_in_vision(k) or ((building_id := get_tile_building_id(k)) is not None and get_entity_type(building_id) == EntityType.GUNNER and get_team(building_id) == my_team)
        }
        for pos, info in self.gunners.items():
            d = info[0]
            for _ in range(3 if d in C.CARDINAL else 2):
                pos = pos.add(d)
                if U.on_the_map(pos):
                    if c.is_in_vision(pos):
                        if get_tile_env(pos) == Environment.WALL:
                            info[1] = True
                            break
                        bb_id = get_tile_builder_bot_id(pos)
                        if bb_id is not None:
                            if c.get_team(bb_id) != my_team:
                                info[1] = False
                                break

                        building_id = get_tile_building_id(pos)
                        e_type = get_entity_type(building_id)
                        if get_team(building_id) == my_team:
                            if e_type in C.TURRET:
                                info[1] = True
                                break
                        else:
                            if e_type not in C.UNIMPORTANT:
                                info[1] = False
                                break
                    else:
                        break
                else:
                    info[1] = True
                    break
            else:
                info[1] = True

        self.to_heal = to_heal

        self.symmetry = symmetry

        if self.enemy_core is None:
            enemy_core: Position | None = None
            x, y = home
            if symmetry & 1:
                candidate: Position = Position(W - 1 - x, H - 1 - y)
                pos = candidate.add(candidate.direction_to(my_pos))
                if c.is_in_vision(pos):
                    building_id = get_tile_building_id(pos)
                    if c.get_team(building_id) == my_team or c.get_entity_type(building_id) != EntityType.CORE:
                        symmetry &= 6

                if symmetry & 1:
                    enemy_core = candidate
            if symmetry & 2:
                candidate: Position = Position(W - 1 - x, y)
                pos = candidate.add(candidate.direction_to(my_pos))
                if c.is_in_vision(pos):
                    building_id = get_tile_building_id(pos)
                    if c.get_team(building_id) == my_team or c.get_entity_type(building_id) != EntityType.CORE:
                        symmetry &= 5

                if symmetry & 2:
                    if enemy_core is None:
                        enemy_core = candidate
                    elif enemy_core != candidate:
                        enemy_core = Position(0, 0)
            if symmetry & 4:
                candidate: Position = Position(x, H - 1 - y)
                pos = candidate.add(candidate.direction_to(my_pos))
                if c.is_in_vision(pos):
                    building_id = get_tile_building_id(pos)
                    if c.get_team(building_id) == my_team or c.get_entity_type(building_id) != EntityType.CORE:
                        symmetry &= 3

                if symmetry & 4:
                    if enemy_core is None:
                        enemy_core = candidate
                    elif enemy_core != candidate:
                        enemy_core = Position(0, 0)

            if enemy_core is not None and enemy_core.x:
                self.enemy_core = enemy_core
        else:
            x0, y0 = home
            x1, y1 = self.enemy_core
            if x0 + x1 != W - 1 or y0 + y1 != H - 1:
                symmetry &= 6
            if x0 != x1 or y0 + y1 != H - 1:
                symmetry &= 5
            if x0 + x1 != W - 1 or y0 != y1:
                symmetry &= 3
        self.symmetry = symmetry

        gunner_covered: int = 0
        gunner_covered_grid = self.gunner_covered_grid = [[False] * C.W for _ in range(C.H)]
        for pos, info in self.gunners.items():
            d, destroy = info
            if not destroy:
                for _ in range(3 if d in C.CARDINAL else 2):
                    pos = pos.add(d)
                    if U.on_the_map(pos):
                        gunner_covered_grid[pos.y][pos.x] = True

        empty: int = self["empty"]
        reach: int = self.reach
        W_plus_1: int = C.W + 1
        for _ in range(50):
            reach |= reach << 1 | reach >> 1
            reach |= reach << W_plus_1 | reach >> W_plus_1
            reach &= empty
        self.reach = reach

    def post_sense(self, c: Controller):
        id_grid: list[list[int]] = self.id_grid
        get_position = c.get_position
        for building_id in c.get_nearby_buildings():
            x, y = get_position(building_id)
            id_grid[y][x] = building_id

    def __getitem__(self, item: str) -> int:
        bitset: list[int] = getattr(self, f"{item}_bitset")
        W_plus_1 = C.W + 1
        return sum(
            row << (y * W_plus_1) for y, row in enumerate(bitset)
        )
