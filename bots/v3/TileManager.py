from cambc import *
from consts import *


class TileManager:
    PASS = {
        EntityType.CONVEYOR,
        EntityType.SPLITTER,
        EntityType.BRIDGE,
        EntityType.ARMOURED_CONVEYOR
    }
    ENV_MAP = {
        Environment.WALL: 0,
        Environment.EMPTY: 1,
        Environment.ORE_TITANIUM: 2,
        Environment.ORE_AXIONITE: 3
    }

    def __init__(self, c: Controller):
        W: int = c.get_map_width()
        H: int = c.get_map_height()
        self.pass_grid: list[int] = [0] * (H + 4)
        self.buildable_grid: list[int] = [0] * (H + 4)
        self.ore_grid: list[int] = [0] * (H + 4)
        self.ally: int = 0
        self.enemy: int = 0
        self.pass_: int = 0
        self.ore: int = 0
        self.buildable: int = 0
        self.build_harvester = [[True] * W for _ in range(H)]
        self.ban_harvester = [[False] * W for _ in range(H)]
        self.env_grid = [[0] * (W + 1) for _ in range(H + 1)]

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

        x, y = my_pos
        clear = -0x200
        if x >= 4:
            clear <<= x - 4
        else:
            clear >>= 4 - x

        pass_grid, buildable_grid, ore_grid, env_grid = self.pass_grid, self.buildable_grid, self.ore_grid, self.env_grid
        W, H = c.get_map_width(), c.get_map_height()
        for yi in range(max(0, y - 4), min(H, y + 5)):
            pass_grid[yi] &= clear
            buildable_grid[yi] &= clear

        ally, enemy = 0, 0
        PASS = TileManager.PASS
        ROAD = EntityType.ROAD
        MARKER = EntityType.MARKER
        CORE = EntityType.CORE
        ENV_MAP = TileManager.ENV_MAP
        for pos in c.get_nearby_tiles():
            xi, yi = pos
            
            building_id = get_tile_building_id(pos)
            env: int = ENV_MAP[get_tile_env(pos)]
            env_grid[yi][xi] = env
            if env >= 2:
                ore_grid[yi] |= 1 << xi
            if building_id is None:
                if env:
                    buildable_grid[yi] |= 1 << xi
            else:
                e_type = get_entity_type(building_id)
                if e_type == ROAD:
                    pass_grid[yi] |= 1 << xi
                    if get_team(building_id) == my_team:
                        buildable_grid[yi] |= 1 << xi
                elif e_type in PASS:
                    pass_grid[yi] |= 1 << xi
                elif e_type == CORE:
                    if get_team(building_id) == my_team:
                        pass_grid[yi] |= 1 << xi
                elif e_type == MARKER:
                    buildable_grid[yi] |= 1 << xi

            bb_id = get_tile_builder_bot_id(pos)
            if bb_id is not None:
                team = c.get_team(bb_id)
                dx = xi - my_pos.x
                dy = yi - my_pos.y
                if team == my_team:
                    ally |= 1 << (dx + dy * 10 + 44)
                else:
                    enemy |= 1 << (dx + dy * 10 + 44)

            if env >= 2:
                if building_id is not None:
                    e_type = get_entity_type(building_id)
                    if e_type == EntityType.HARVESTER and pos.distance_squared(my_pos) <= 13:
                        self.build_harvester[yi][xi] = False
                        if self.ban_harvester[yi][xi]:
                            continue

                        if pos.distance_squared(home) <= 5:
                            continue
                        has_space, has_conveyor = False, False
                        for d in CARDINAL:
                            cur: Position = pos.add(d)
                            if 0 <= cur.x <= W - 1 and 0 <= cur.y <= H - 1:
                                building_id = c.get_tile_building_id(cur)
                                if building_id is None:
                                    has_space |= c.get_tile_env(cur) == Environment.EMPTY
                                else:
                                    if c.get_team(building_id) != my_team:
                                        continue
                                    e_type = c.get_entity_type(building_id)
                                    if e_type in CONVEYOR_VARIANT:
                                        has_conveyor = True
                                        break
                                    elif e_type == EntityType.ROAD or e_type == EntityType.MARKER:
                                        has_space = True
                        if has_conveyor or not has_space:
                            continue

                        self.build_harvester[yi][xi] = True

        self.ally = ally & -0x100000000001
        self.enemy = enemy
        self.pass_ = self.get_vision(x, y, self.pass_grid)
        self.buildable = self.get_vision(x, y, self.buildable_grid)
        self.ore = self.get_vision(x, y, self.ore_grid)
