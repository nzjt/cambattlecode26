from cambc import *
import consts as C
import utils as U
from Wander import Wander


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
        self.had_building_bitset: list[int] = [0] * H
        self.has_building_bitset: list[int] = [0] * H
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
        self.conveyors: set[Position] = set()
        self.gunners: dict[Position, bool] = {}
        self.gunner_covered: int = 0

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

        my_id = c.get_id()
        my_pos: Position = c.get_position(my_id)
        my_team = get_team(my_id)

        self.see_gun = False
        for building_id in c.get_nearby_buildings(9):
            if c.get_entity_type(building_id) == EntityType.GUNNER and c.get_team(building_id) == my_team:
                self.see_gun = True

        pass_bitset, buildable_bitset, ore_bitset, barrier_bitset = self.pass_bitset, self.buildable_bitset, self.ore_bitset, self.barrier_bitset
        empty_bitset: list[int] = self.empty_bitset
        titanium_bitset: list[int] = self.titanium_bitset
        conveyor_bitset: list[int] = self.conveyor_bitset
        had_building_bitset: list[int] = self.had_building_bitset
        has_building_bitset: list[int] = self.has_building_bitset
        env_grid, pass_grid = self.env_grid, self.pass_grid
        building_grid: list[list[tuple[EntityType, ...] | None]] = self.building_grid
        x, y = my_pos
        if x >= 4:
            shift = x - 4
            for mask, yi in [(0x7c, y - 4), (0xfe, y - 3), (0x1ff, y - 2), (0x1ff, y - 1), (0x1ff, y), (0x1ff, y + 1), (0x1ff, y + 2), (0xfe, y + 3), (0x7c, y + 4)]:
                if 0 <= yi < C.H:
                    mask = ~(mask << shift)
                    pass_bitset[yi] &= mask
                    buildable_bitset[yi] &= mask
                    barrier_bitset[yi] &= mask
                    has_building_bitset[yi] &= mask
        else:
            shift = 4 - x
            for mask, yi in [(0x7c, y - 4), (0xfe, y - 3), (0x1ff, y - 2), (0x1ff, y - 1), (0x1ff, y), (0x1ff, y + 1), (0x1ff, y + 2), (0xfe, y + 3), (0x7c, y + 4)]:
                if 0 <= yi < C.H:
                    mask = ~(mask >> shift)
                    pass_bitset[yi] &= mask
                    buildable_bitset[yi] &= mask
                    barrier_bitset[yi] &= mask
                    has_building_bitset[yi] &= mask

        # for yi in range(max(0, y - 4), min(C.H, y + 5)):

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

        conveyors: set[Position] = self.conveyors

        gunners: dict[Position, bool] = self.gunners

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
                    if self.ban_harvester[yi][xi]:
                        self.build_harvester[yi][xi] = False
                    elif building_id is not None:
                        e_type = get_entity_type(building_id)
                        if e_type == EntityType.HARVESTER:
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
                if e_type == ROAD:
                    pass_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = 2
                    if get_team(building_id) == my_team:
                        buildable_bitset[yi] |= 1 << xi
                elif e_type in CONVEYOR_VARIANT:
                    pass_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = 2
                    if get_team(building_id) == my_team:
                        env_grid[yi][xi] = 3
                        conveyors.add(pos)
                        conveyor_bitset[yi] |= 1 << xi
                        had_building_bitset[yi] |= 1 << xi
                        has_building_bitset[yi] |= 1 << xi
                        if e_type == EntityType.BRIDGE:
                            building_grid[yi][xi] = (e_type, c.get_bridge_target(building_id))
                        else:
                            building_grid[yi][xi] = (e_type, get_direction(building_id))
                        if my_pos.distance_squared(pos) <= 10:
                            wander_seen.add(pos)
                            wander_unseen.discard(pos)
                        elif pos not in wander.seen:
                            wander.unseen.add(pos)
                elif e_type == BARRIER:
                    pass_grid[yi][xi] = 0
                    if get_team(building_id) == my_team:
                        barrier_bitset[yi] |= 1 << xi
                elif e_type == CORE:
                    if get_team(building_id) == my_team:
                        pass_bitset[yi] |= 1 << xi
                        pass_grid[yi][xi] = 2
                    else:
                        pass_grid[yi][xi] = 0
                elif e_type == MARKER:
                    buildable_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = 1
                elif e_type == GUNNER:
                    pass_grid[yi][xi] = 0
                    if get_team(building_id) == my_team:
                        if pos not in gunners:
                            gunners[pos] = False
                        if pos.distance_squared(self.home) <= 8:
                            if pos.add(c.get_direction(building_id)).distance_squared(self.home) <= 8:
                                self.has_kill_chamber = True
                else:
                    pass_grid[yi][xi] = 0

            bb_id = get_tile_builder_bot_id(pos)
            if bb_id is not None:
                team = c.get_team(bb_id)
                dx = xi - my_pos.x
                dy = yi - my_pos.y
                if team == my_team:
                    ally |= 1 << (dx + dy * 10 + 44)
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

        def destroy_gunner(pos: Position, building_id: int) -> bool:
            d: Direction = c.get_direction(building_id)
            for _ in range(3 if d in C.CARDINAL else 2):
                pos = pos.add(d)
                if U.on_the_map(pos):
                    if c.is_in_vision(pos):
                        if get_tile_env(pos) == Environment.WALL:
                            return True
                        building_id = get_tile_building_id(pos)
                        e_type = get_entity_type(building_id)
                        if get_team(building_id) != my_team and e_type != EntityType.MARKER:
                            return False
                    else:
                        return False
                else:
                    return True

            return True

        self.gunners = {
            pos: destroy_gunner(pos, building_id) if visible else gunners[pos] for pos in gunners if not (visible := c.is_in_vision(pos)) or (
                        (building_id := get_tile_building_id(pos)) is not None and get_entity_type(
                    building_id) == EntityType.GUNNER and get_team(building_id) == my_team)
        }
        gunner_covered: int = 0

    def __getitem__(self, item: str) -> int:
        bitset: list[int] = getattr(self, f"{item}_bitset")
        W_plus_1 = C.W + 1
        return sum(
            row << (y * W_plus_1) for y, row in enumerate(bitset)
        )
