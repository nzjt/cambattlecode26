from cambc import *
import consts as C
import utils as U
from Wander import Wander
from DynamicConnectivity import DynamicConnectivity


class TileManager:
    ENV_MAP = {
        Environment.WALL: 1,
        Environment.EMPTY: 2,
        Environment.ORE_TITANIUM: 4,
        Environment.ORE_AXIONITE: 5
    }

    def __init__(self, home: Position):
        W, H = C.W, C.H
        H_plus_4 = H + 4
        self.home: Position = home
        self.pass_bitset: list[int] = [0] * H_plus_4
        self.buildable_bitset: list[int] = [0] * H_plus_4
        self.barrier_bitset: list[int] = [0] * H_plus_4
        self.ore_bitset: list[int] = [0] * H_plus_4
        self.empty_bitset: list[int] = [0] * H
        self.titanium_bitset: list[int] = [0] * H
        self.conveyor_bitset: list[int] = [0] * H
        self.bridge_bitset: list[int] = [0] * H
        self.had_building_bitset: list[int] = [0] * H
        self.has_building_bitset: list[int] = [0] * H
        self.unit_bitset: list[int] = []
        self.building_grid: list[list[tuple[EntityType, ...] | None]] = [[None] * W for _ in range(H)]
        self.ally: int = 0
        self.enemy: int = 0
        self.pass_: int = 0
        self.ore: int = 0
        self.buildable: int = 0
        self.barrier: int = 0
        self.build_harvester = [[True] * W for _ in range(H)]
        self.ban_harvester = [[False] * W for _ in range(H)]
        self.env_grid = [[0] * W for _ in range(H)]
        self.pass_grid: list[list[int]] = [[1] * W for _ in range(H)]
        self.see_gun: bool = False
        self.bot_tracker: dict[int, tuple[Position, int, int]] = {}
        self.has_kill_chamber: bool = False
        self.axionite_ores: set[Position] = set()
        self.gunners: dict[Position, list] = {}
        self.gunner_covered_grid: list[list[bool]] = []
        self.gunner_covered: int = 0
        self.enemy_core: Position | None = None
        self.dynamic_connectivity: DynamicConnectivity = DynamicConnectivity()
        self.symmetry: int = 7
        self.my_ores: set[Position] = set()
        self.enemy_ores: set[Position] = set()
        self.to_heal: set[Position] = set()

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

    def get_vision(self, x: int, y: int, grid: list[int]) -> int:
        only_9 = 0x1ff
        if x >= 4:
            shift = x - 4
            return (grid[y - 4] >> shift & only_9 |
                    (grid[y - 3] >> shift & only_9) << 10 |
                    (grid[y - 2] >> shift & only_9) << 20 |
                    (grid[y - 1] >> shift & only_9) << 30 |
                    (grid[y] >> shift & only_9) << 40 |
                    (grid[y + 1] >> shift & only_9) << 50 |
                    (grid[y + 2] >> shift & only_9) << 60 |
                    (grid[y + 3] >> shift & only_9) << 70 |
                    (grid[y + 4] >> shift & only_9) << 80)
        else:
            shift = 4 - x
            return (grid[y - 4] << shift & only_9 |
                    (grid[y - 3] << shift & only_9) << 10 |
                    (grid[y - 2] << shift & only_9) << 20 |
                    (grid[y - 1] << shift & only_9) << 30 |
                    (grid[y] << shift & only_9) << 40 |
                    (grid[y + 1] << shift & only_9) << 50 |
                    (grid[y + 2] << shift & only_9) << 60 |
                    (grid[y + 3] << shift & only_9) << 70 |
                    (grid[y + 4] << shift & only_9) << 80)

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
        pass_bitset, buildable_bitset, ore_bitset, barrier_bitset = self.pass_bitset, self.buildable_bitset, self.ore_bitset, self.barrier_bitset
        empty_bitset: list[int] = self.empty_bitset
        titanium_bitset: list[int] = self.titanium_bitset
        conveyor_bitset: list[int] = self.conveyor_bitset
        bridge_bitset: list[int] = self.bridge_bitset
        had_building_bitset: list[int] = self.had_building_bitset
        has_building_bitset: list[int] = self.has_building_bitset
        unit_bitset = self.unit_bitset = [0] * H
        env_grid, pass_grid = self.env_grid, self.pass_grid
        building_grid: list[list[tuple[EntityType, ...] | None]] = self.building_grid
        x, y = my_pos
        if x >= 4:
            shift = x - 4
            for mask, yi in [(0x7c, y - 4), (0xfe, y - 3), (0x1ff, y - 2), (0x1ff, y - 1), (0x1ff, y), (0x1ff, y + 1), (0x1ff, y + 2), (0xfe, y + 3), (0x7c, y + 4)]:
                if 0 <= yi < H:
                    mask = ~(mask << shift)
                    pass_bitset[yi] &= mask
                    buildable_bitset[yi] &= mask
                    barrier_bitset[yi] &= mask
                    has_building_bitset[yi] &= mask
        else:
            shift = 4 - x
            for mask, yi in [(0x7c, y - 4), (0xfe, y - 3), (0x1ff, y - 2), (0x1ff, y - 1), (0x1ff, y), (0x1ff, y + 1), (0x1ff, y + 2), (0xfe, y + 3), (0x7c, y + 4)]:
                if 0 <= yi < H:
                    mask = ~(mask >> shift)
                    pass_bitset[yi] &= mask
                    buildable_bitset[yi] &= mask
                    barrier_bitset[yi] &= mask
                    has_building_bitset[yi] &= mask

        ally, enemy = 0, 0
        ROAD = EntityType.ROAD
        BARRIER = EntityType.BARRIER
        MARKER = EntityType.MARKER
        CORE = EntityType.CORE
        ENV_MAP = TileManager.ENV_MAP
        GUNNER = EntityType.GUNNER
        CONVEYOR_VARIANT = C.CONVEYOR_VARIANT

        bot_tracker = self.bot_tracker
        round = c.get_current_round()

        wander_seen = wander.seen
        wander_unseen = wander.unseen

        gunners: dict[Position, list] = self.gunners

        dynamic_connectivity: DynamicConnectivity = self.dynamic_connectivity

        symmetry: int = self.symmetry

        my_ores: set[Position] = self.my_ores
        enemy_ores: set[Position] = self.enemy_ores

        to_heal: set[Position] = {pos for pos in self.to_heal if not c.is_in_vision(pos) or c.get_hp(building_id := c.get_tile_building_id(pos)) < c.get_max_hp(building_id)}

        for pos in c.get_nearby_tiles():
            xi, yi = pos

            building_id = get_tile_building_id(pos)
            env: int = ENV_MAP[get_tile_env(pos)]
            env_grid[yi][xi] = env
            if env == 2:
                empty_bitset[yi] |= 1 << xi
            elif env >= 4:
                ore_bitset[yi] |= 1 << xi
                if env == 4:
                    titanium_bitset[yi] |= 1 << xi
                    is_mine: bool = True
                    if self.ban_harvester[yi][xi]:
                        self.build_harvester[yi][xi] = False
                    elif building_id is not None:
                        e_type = get_entity_type(building_id)
                        if e_type == EntityType.HARVESTER:
                            if get_team(building_id) != my_team:
                                is_mine = False
                            self.build_harvester[yi][xi] = False
                            if pos.distance_squared(my_pos) <= 13:
                                if pos.distance_squared(home) > 5:
                                    has_space, has_conveyor = False, False
                                    for d in C.CARDINAL:
                                        cur: Position = pos.add(d)
                                        if U.on_the_map(cur):
                                            b_id = c.get_tile_building_id(cur)
                                            if b_id is None:
                                                has_space |= c.get_tile_env(cur) == Environment.EMPTY
                                            else:
                                                if c.get_team(b_id) != my_team:
                                                    continue
                                                e_type = c.get_entity_type(b_id)
                                                if e_type in C.CONVEYOR_VARIANT:
                                                    has_conveyor = True
                                                    break
                                                elif e_type == EntityType.ROAD or e_type == EntityType.MARKER:
                                                    has_space = True
                                    if not has_conveyor and has_space:
                                        self.build_harvester[yi][xi] = True
                        i: int = y * W + x
                        if i not in dynamic_connectivity.harvesters:
                            for d in C.CARDINAL:
                                cur: Position = pos.add(d)
                                if U.is_visible(cur):
                                    b_id = c.get_tile_building_id(cur)
                                    if get_entity_type(b_id) in C.CONVEYOR_VARIANT and c.get_team(b_id) == my_team:
                                        dynamic_connectivity.add_harvester(i)
                                        xj, yj = cur
                                        j: int = yj * W + xj
                                        dynamic_connectivity.merge(i, j)
                                        break
                        if is_mine:
                            my_ores.add(pos)
                            enemy_ores.discard(pos)
                        else:
                            enemy_ores.add(pos)
                            my_ores.discard(pos)
                else:
                    if self.ban_harvester[yi][xi]:
                        self.build_harvester[yi][xi] = False
                        self.axionite_ores.discard(pos)
                    elif building_id is not None and c.get_entity_type(building_id) == EntityType.HARVESTER:
                        self.build_harvester[yi][xi] = False
                        self.axionite_ores.discard(pos)
                    else:
                        self.axionite_ores.add(pos)
            if building_id is None:
                if env >= 2:
                    buildable_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = 1
                else:
                    pass_grid[yi][xi] = 0
            else:
                e_type: EntityType = get_entity_type(building_id)
                team: Team = c.get_team(building_id)
                if e_type == ROAD:
                    pass_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = 2
                    if team == my_team:
                        buildable_bitset[yi] |= 1 << xi
                elif e_type in CONVEYOR_VARIANT:
                    pass_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = 2
                    if team == my_team:
                        if c.get_hp(building_id) < c.get_max_hp(building_id):
                            to_heal.add(pos)
                        env_grid[yi][xi] = 3
                        had_building_bitset[yi] |= 1 << xi
                        has_building_bitset[yi] |= 1 << xi
                        if e_type == EntityType.BRIDGE:
                            nxt: Position = c.get_bridge_target(building_id)
                            building_grid[yi][xi] = (e_type, nxt)
                            bridge_bitset[yi] |= 1 << xi
                        else:
                            d: Direction = get_direction(building_id)
                            building_grid[yi][xi] = (e_type, d)
                            nxt = pos.add(d)
                            conveyor_bitset[yi] |= 1 << xi
                        if U.on_the_map(nxt):
                            i: int = yi * W + xi
                            xj, yj = nxt
                            j: int = yj * W + xj
                            dynamic_connectivity.merge(i, j)
                        if my_pos.distance_squared(pos) <= 10:
                            wander_seen.add(pos)
                            wander_unseen.discard(pos)
                        elif pos not in wander.seen:
                            wander.unseen.add(pos)
                elif e_type == BARRIER:
                    pass_grid[yi][xi] = 0
                    if team == my_team:
                        if c.get_hp(building_id) < 30:
                            to_heal.add(pos)
                        barrier_bitset[yi] |= 1 << xi
                elif e_type == CORE:
                    if team == my_team:
                        if c.get_hp(building_id) < 500:
                            to_heal.add(pos)
                        pass_bitset[yi] |= 1 << xi
                        pass_grid[yi][xi] = 2
                    else:
                        pass_grid[yi][xi] = 0
                        self.enemy_core = c.get_position(building_id)
                elif e_type == MARKER:
                    buildable_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = 1
                    if self.enemy_core is None:
                        if team == my_team:
                            symmetry &= get_marker_value(building_id)
                elif e_type == GUNNER:
                    pass_grid[yi][xi] = 0
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
                    pass_grid[yi][xi] = 0
                    if team == my_team:
                        if c.get_hp(building_id) < c.get_max_hp(building_id):
                            to_heal.add(pos)

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

        self.ally = ally & -0x100000000001
        self.enemy = enemy
        self.pass_ = self.get_vision(x, y, self.pass_bitset)
        self.buildable = self.get_vision(x, y, self.buildable_bitset)
        self.ore = self.get_vision(x, y, self.ore_bitset)
        self.barrier = self.get_vision(x, y, self.barrier_bitset)

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

    def __getitem__(self, item: str) -> int:
        bitset: list[int] = getattr(self, f"{item}_bitset")
        W_plus_1 = C.W + 1
        return sum(
            row << (y * W_plus_1) for y, row in enumerate(bitset)
        )
