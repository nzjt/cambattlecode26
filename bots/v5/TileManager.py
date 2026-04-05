from cambc import *
import consts as C
import utils as U


class TileManager:
    PASS = {
        EntityType.CONVEYOR,
        EntityType.SPLITTER,
        EntityType.BRIDGE,
        EntityType.ARMOURED_CONVEYOR
    }
    ENV_MAP = {
        Environment.WALL: 1,
        Environment.EMPTY: 2,
        Environment.ORE_TITANIUM: 3,
        Environment.ORE_AXIONITE: 4
    }

    def __init__(self, home: Position):
        W: int = C.W
        H_plus_4 = C.H + 4
        self.home: Position = home
        self.enemy_core: Position | None = None
        self.pass_bitset: list[int] = [0] * H_plus_4
        self.buildable_bitset: list[int] = [0] * H_plus_4
        self.barrier_bitset: list[int] = [0] * H_plus_4
        self.ore_grid: list[int] = [0] * H_plus_4
        self.ally: int = 0
        self.enemy: int = 0
        self.pass_: int = 0
        self.ore: int = 0
        self.buildable: int = 0
        self.barrier: int = 0
        self.build_harvester = [[True] * W for _ in range(C.H)]
        self.ban_harvester = [[False] * W for _ in range(C.H)]
        self.env_grid = [[0] * W for _ in range(C.H)]
        self.pass_grid: list[list[bool]] = [[True] * W for _ in range(C.H)]
        self.see_gun: bool = False
        self.bot_tracker: dict[int, tuple[Position, int, int]] = {}
        self.protected: list[list[bool]] = []
        self.has_kill_chamber: bool = False

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

    def sense(self, c: Controller, home: Position):
        get_tile_building_id = c.get_tile_building_id
        get_tile_env = c.get_tile_env
        get_entity_type = c.get_entity_type
        get_tile_builder_bot_id = c.get_tile_builder_bot_id
        get_team = c.get_team

        my_id = c.get_id()
        my_pos: Position = c.get_position(my_id)
        my_team = get_team(my_id)

        self.see_gun = False
        for building_id in c.get_nearby_buildings(9):
            if c.get_entity_type(building_id) == EntityType.GUNNER and c.get_team(building_id) == my_team:
                self.see_gun = True

        x, y = my_pos
        clear = -0x200
        if x >= 4:
            clear <<= x - 4
        else:
            clear >>= 4 - x

        pass_bitset, buildable_bitset, ore_bitset, barrier_bitset = self.pass_bitset, self.buildable_bitset, self.ore_grid, self.barrier_bitset
        env_grid, pass_grid = self.env_grid, self.pass_grid
        for yi in range(max(0, y - 4), min(C.H, y + 5)):
            pass_bitset[yi] &= clear
            buildable_bitset[yi] &= clear
            barrier_bitset[yi] &= clear

        ally, enemy = 0, 0
        PASS = TileManager.PASS
        ROAD = EntityType.ROAD
        BARRIER = EntityType.BARRIER
        MARKER = EntityType.MARKER
        CORE = EntityType.CORE
        ENV_MAP = TileManager.ENV_MAP
        LAUNCHER = EntityType.LAUNCHER
        GUNNER = EntityType.GUNNER

        bot_tracker = self.bot_tracker
        round = c.get_current_round()

        W_plus_1: int = C.W + 1
        protected = self.protected = [[False] * W_plus_1 for _ in range(C.H)]

        enemy_core_hash: int = 0
        for pos in c.get_nearby_tiles():
            xi, yi = pos
            
            building_id = get_tile_building_id(pos)
            env: int = ENV_MAP[get_tile_env(pos)]
            env_grid[yi][xi] = env
            if env >= 3:
                ore_bitset[yi] |= 1 << xi
            if building_id is None:
                if env >= 2:
                    buildable_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = True
                else:
                    pass_grid[yi][xi] = False
            else:
                e_type = get_entity_type(building_id)
                if e_type == ROAD:
                    pass_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = True
                    if get_team(building_id) == my_team:
                        buildable_bitset[yi] |= 1 << xi
                elif e_type == BARRIER:
                    pass_grid[yi][xi] = False
                    if get_team(building_id) == my_team:
                        barrier_bitset[yi] |= 1 << xi
                elif e_type in PASS:
                    pass_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = True
                elif e_type == CORE:
                    if get_team(building_id) == my_team:
                        pass_bitset[yi] |= 1 << xi
                        pass_grid[yi][xi] = True
                    else:
                        pass_grid[yi][xi] = False
                        self.enemy_core = c.get_position(building_id)
                elif e_type == MARKER:
                    buildable_bitset[yi] |= 1 << xi
                    pass_grid[yi][xi] = True
                    if get_team(building_id) == my_team:
                        enemy_core_hash = c.get_marker_value(building_id)
                elif e_type == LAUNCHER:
                    pass_grid[yi][xi] = False
                    for yj in range(yi - 1, yi + 2):
                        for xj in range(xi - 1, xi + 2):
                            protected[yj][xj] = True
                elif e_type == GUNNER:
                    pass_grid[yi][xi] = False
                    if get_team(building_id) == my_team:
                        if pos.distance_squared(self.home) <= 8:
                            if pos.add(c.get_direction(building_id)).distance_squared(self.home) <= 8:
                                self.has_kill_chamber = True
                else:
                    pass_grid[yi][xi] = False

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

            if env == 3:
                if self.ban_harvester[yi][xi]:
                    self.build_harvester[yi][xi] = False
                elif building_id is not None:
                    e_type = get_entity_type(building_id)
                    if e_type == EntityType.HARVESTER:
                        self.build_harvester[yi][xi] = False
                        if pos.distance_squared(my_pos) <= 13:
                            if pos.distance_squared(home) <= 5:
                                continue
                            has_space, has_conveyor = False, False
                            for d in C.CARDINAL:
                                cur: Position = pos.add(d)
                                if U.on_the_map(cur):
                                    building_id = c.get_tile_building_id(cur)
                                    if building_id is None:
                                        has_space |= c.get_tile_env(cur) == Environment.EMPTY
                                    else:
                                        if c.get_team(building_id) != my_team:
                                            continue
                                        e_type = c.get_entity_type(building_id)
                                        if e_type in C.CONVEYOR_VARIANT:
                                            has_conveyor = True
                                            break
                                        elif e_type == EntityType.ROAD or e_type == EntityType.MARKER:
                                            has_space = True
                            if has_conveyor or not has_space:
                                continue

                            self.build_harvester[yi][xi] = True

        self.ally = ally & -0x100000000001
        self.enemy = enemy
        self.pass_ = self.get_vision(x, y, self.pass_bitset)
        self.buildable = self.get_vision(x, y, self.buildable_bitset)
        self.ore = self.get_vision(x, y, self.ore_grid)
        self.barrier = self.get_vision(x, y, self.barrier_bitset)

        if enemy_core_hash:
            self.enemy_core = Position(enemy_core_hash >> 6, enemy_core_hash & 63)
