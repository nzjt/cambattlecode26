import random
from cambc import *
from Unit import Unit
from Movement import Movement
from Nav import Nav
from Bug0Better import Bug0Better
from ConveyorManager import ConveyorManager
from TileManager import TileManager
from Bfs import Bfs
from consts import *


class BuilderBot(Unit):
    def __init__(self):
        self.movement: Movement | None = None
        self.tile_manager: TileManager | None = None
        self.nav: Nav = Bug0Better()
        self.home: Position | None = None
        self.target: Position | None = None
        self.target_type: int = 0  # 0: nothing, 1: explore, 2: go to ore, 3: build conveyor home, 4: destroy enemy conveyors
        self.target_dist: int = 0
        self.conveyor_manager: ConveyorManager | None = None
        self.expiry: int = 0
        self.bfs: Bfs | None = None

    def sense(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        W, H = c.get_map_width(), c.get_map_height()
        x, y = my_pos

        if self.target_type == 4:
            self.target_type = 0

            dist = my_pos.distance_squared(self.target)
            xi, yi = self.target
            if dist <= 13 and self.bfs.can_reach_adj(xi - x, yi - y):
                building_id = c.get_tile_building_id(self.target)
                if c.get_team(building_id) != my_team and c.get_entity_type(building_id) == EntityType.HARVESTER:
                    has_space, has_enemy = False, False
                    for d in CARDINAL:
                        nxt = self.target.add(d)
                        if 0 <= nxt.x < W and 0 <= nxt.y < H:
                            building_id = c.get_tile_building_id(nxt)
                            if building_id is None:
                                has_space = True
                            elif c.get_team(building_id) == my_team:
                                e_type = c.get_entity_type(building_id)
                                if e_type == EntityType.SENTINEL:
                                    has_enemy = False
                                    break
                                else:
                                    has_space |= e_type in UNIMPORTANT
                            else:
                                has_enemy |= c.get_entity_type(building_id) != EntityType.MARKER

                    if has_space and has_enemy:
                        self.target_type = 4

        if self.target_type == 4:
            pass
        elif self.target_type == 3:
            retargets: list[Position] = []
            for pos in c.get_nearby_tiles():
                building_id = c.get_tile_building_id(pos)
                if c.get_entity_type(building_id) in MONOCHILD_CONVEYOR and c.get_team(building_id) == my_team:
                    xi, yi = pos
                    if self.conveyor_manager.path_index[yi][xi] >= self.conveyor_manager.index:
                        good = True
                        cur = pos
                        for _ in range(10):
                            building_id = c.get_tile_building_id(cur)
                            if building_id is None or c.get_team(building_id) != my_team:
                                good = False
                                break
                            e_type = c.get_entity_type(building_id)
                            if e_type in CONVEYOR:
                                cur = cur.add(c.get_direction(building_id))
                            elif e_type == EntityType.BRIDGE:
                                cur = c.get_bridge_target(building_id)
                            else:
                                good = e_type == EntityType.CORE
                                break

                            if c.is_in_vision(cur):
                                if self.conveyor_manager.path_index[cur.y][cur.x] < self.conveyor_manager.index:
                                    good = False
                                    break
                            else:
                                # Probably fine?
                                break

                        if good:
                            retargets.append(pos)

            self.conveyor_manager.retarget(c, retargets, self.tile_manager)
        else:
            for pos in c.get_nearby_tiles():
                env: Environment = c.get_tile_env(pos)
                if env == Environment.ORE_TITANIUM or env == Environment.ORE_AXIONITE:
                    building_id = c.get_tile_building_id(pos)
                    if c.get_entity_type(building_id) == EntityType.HARVESTER:
                        dist = my_pos.distance_squared(pos)
                        xi, yi = pos
                        if dist <= 13 and self.bfs.can_reach_adj(xi - x, yi - y):
                            has_space, has_enemy = False, False
                            for d in CARDINAL:
                                nxt = pos.add(d)
                                if 0 <= nxt.x < W and 0 <= nxt.y < H:
                                    building_id = c.get_tile_building_id(nxt)
                                    if building_id is None:
                                        has_space = True
                                    elif c.get_team(building_id) == my_team:
                                        e_type = c.get_entity_type(building_id)
                                        if e_type == EntityType.SENTINEL:
                                            has_enemy = False
                                            break
                                        else:
                                            has_space |= e_type in UNIMPORTANT
                                    else:
                                        has_enemy |= c.get_entity_type(building_id) != EntityType.MARKER

                            if has_space and has_enemy:
                                self.target = pos
                                self.target_type = 4
                                break

                    if self.tile_manager.build_harvester[pos.y][pos.x] and self.target_type <= 2:
                        if c.get_tile_builder_bot_id(pos) is not None:
                            continue

                        dist = my_pos.distance_squared(pos)
                        if self.target_type == 2:
                            if dist >= self.target_dist:
                                break

                        self.target = pos
                        self.target_type = 2
                        self.target_dist = dist
                        self.conveyor_manager = None

    def run(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position()
        my_team = c.get_team()

        if self.home is None:
            self.home = c.get_position(c.get_tile_building_id(my_pos))
            self.movement = Movement()
            self.tile_manager = TileManager(c)
            self.bfs = Bfs(self.tile_manager)

        if self.target_type == 1:
            if my_pos.distance_squared(self.target) <= 4 or c.get_current_round() > self.expiry:
                self.target_type = 0
        elif self.target_type == 2:
            if c.is_in_vision(self.target):
                bb_id = c.get_tile_builder_bot_id(self.target)
                if bb_id is not None and bb_id != my_id:
                    self.target_type = 0
        elif self.target_type == 3:
            if self.conveyor_manager.done:
                self.target_type = 0
            else:
                self.conveyor_manager.update_index(c)

        self.tile_manager.sense(c, self.home)
        self.bfs.update(c, self.conveyor_manager)

        if self.target_type == 2:
            if not self.tile_manager.build_harvester[self.target.y][self.target.x]:
                self.target_type = 0

            if self.target_type:
                print("hm", self.target)
                dist = my_pos.distance_squared(self.target)
                self.target_dist = min(self.target_dist, dist)

                if dist == 0:
                    self.target = self.home
                    self.target_type = 3
                    self.target_dist = my_pos.distance_squared(self.target)
                    self.conveyor_manager = ConveyorManager(c, self.tile_manager, my_pos, self.target)
                elif dist == 1:
                    building_id = c.get_tile_building_id(self.target)
                    if c.get_entity_type(building_id) == EntityType.HARVESTER:
                        harvester: Position = self.target
                        self.target = self.home
                        self.target_type = 3
                        self.target_dist = my_pos.distance_squared(self.target)
                        self.conveyor_manager = ConveyorManager(c, self.tile_manager, harvester, self.target)

        self.sense(c)
        self.movement.upd(c)

        if c.get_hp(my_id) < c.get_max_hp(my_id) and c.can_heal(my_pos):
            c.heal(my_pos)

        if self.target_type == 0:
            self.target = Position(random.randint(0, c.get_map_width() - 1), random.randint(0, c.get_map_height() - 1))
            self.target_type = 1
            self.expiry = c.get_current_round() + 260

        if self.target_type == 1:
            c.draw_indicator_line(my_pos, self.target, 255, 0, 0)
            self.nav.move(c, self.target, self.movement)
        elif self.target_type == 2:
            c.draw_indicator_line(my_pos, self.target, 0, 255, 0)
            self.nav.move(c, self.target, self.movement)
        elif self.target_type == 3:
            self.conveyor_manager.update(c, self.movement, self.tile_manager, self.bfs)
        elif self.target_type == 4:
            W, H = c.get_map_width(), c.get_map_height()
            sentinel_targets: list[Position] = []
            for d in CARDINAL:
                nxt = self.target.add(d)
                if 0 <= nxt.x < W and 0 <= nxt.y < H:
                    building_id = c.get_tile_building_id(nxt)
                    if building_id is None or c.get_team(building_id) == my_team and c.get_entity_type(building_id) in UNIMPORTANT:
                        sentinel_targets.append(nxt)

            x, y = my_pos
            deltas = [(xi - x, yi - y) for xi, yi in sentinel_targets]
            d: Direction = self.bfs.bfs_adj_exc_multi(deltas, self.tile_manager.pass_)

            if d is None:
                d = self.bfs.bfs_adj_exc_multi(deltas, self.tile_manager.pass_ | self.tile_manager.buildable)

            if d is None:
                # :(
                pass
            elif d != Direction.CENTRE and self.movement.can_move(d):
                self.movement.move(d)
                my_pos = c.get_position()
            c.draw_indicator_line(my_pos, self.target, 255, 128, 0)

            if c.get_global_resources()[0] >= c.get_sentinel_cost()[0]:
                for target in sentinel_targets:
                    if my_pos.distance_squared(target) <= 2:
                        if c.can_destroy(target):
                            c.destroy(target)
                        if c.can_build_sentinel(target, Direction.NORTH):
                            d = target.direction_to(self.target)
                            if self.target.add(d.rotate_left()).distance_squared(self.home) > self.target.add(d.rotate_right()).distance_squared(self.home):
                                d = d.rotate_left()
                            else:
                                d = d.rotate_right()
                            c.build_sentinel(target, d)
                            self.target_type = 0
                            break
