import random
from lib2to3.pgen2.literals import simple_escapes

from cambc import *
from Unit import Unit
from Movement import Movement
from Nav import Nav
from Bug0Better import Bug0Better
from ConveyorManager import ConveyorManager
from TileManager import TileManager
from Bfs import Bfs
from FoundryManager import FoundryManager
from AStarNav import AStarNav
from consts import *


class BuilderBot(Unit):
    def __init__(self):
        self.birth: int = 0
        self.movement: Movement | None = None
        self.tile_manager: TileManager | None = None
        self.nav: Nav | None = None
        self.home: Position | None = None
        self.target: Position | None = None
        self.sub_target: Position | None = None
        self.target_type: int = 0  # 0: nothing, 1: explore, 2: go to ore, 3: build conveyor home, 4: destroy enemy conveyors, 5: repair conveyor
        self.target_dist: int = 0
        self.conveyor_manager: ConveyorManager | None = None
        self.expiry: int = 0
        self.bfs: Bfs | None = None
        self.foundry_manager: FoundryManager | None = None
        self.is_troll: bool = False
        self.has_econ: bool = False
        self.prev_resources: int = 1000
        self.has_harvester: bool = False

    def sense(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        W, H = c.get_map_width(), c.get_map_height()
        x, y = my_pos

        def needs_repair(pos: Position, trustworthy: bool = False) -> bool:
            if c.is_in_vision(pos):
                building_id = c.get_tile_building_id(pos)
                if c.get_team(building_id) == my_team:
                    e_type = c.get_entity_type(building_id)
                    if e_type in CONVEYOR:
                        if c.get_stored_resource(building_id) is not None:
                            d: Direction = c.get_direction(building_id)
                            nxt = pos.add(d)
                            if c.is_in_vision(nxt):
                                building_id = c.get_tile_building_id(nxt)
                                if building_id is not None and c.get_team(building_id) == my_team and c.get_entity_type(building_id) not in UNIMPORTANT:
                                    return False
                                if not trustworthy:
                                    for e in Direction:
                                        nxt = pos.add(e)
                                        if 0 <= nxt.x < W and 0 <= nxt.y < H:
                                            bb_id = c.get_tile_builder_bot_id(nxt)
                                            if bb_id is not None and bb_id != my_id and c.get_team(bb_id) == my_team:
                                                return False
                                return True
                            return trustworthy
                return False
            else:
                return trustworthy

        if self.target_type == 4:
            dist = my_pos.distance_squared(self.target)
            xi, yi = self.target
            if dist <= 13 and self.bfs.can_reach_adj(xi - x, yi - y):
                self.target_type = 0
                building_id = c.get_tile_building_id(self.target)
                if c.get_team(building_id) != my_team and c.get_entity_type(building_id) == EntityType.HARVESTER:
                    has_space, has_enemy = False, False
                    for d in CARDINAL:
                        nxt = self.target.add(d)
                        if 0 <= nxt.x < W and 0 <= nxt.y < H:
                            building_id = c.get_tile_building_id(nxt)
                            if building_id is None:
                                has_space = c.get_tile_env(nxt) != Environment.WALL
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
        elif self.target_type == 5:
            if self.conveyor_manager is None and not needs_repair(self.target, True):
                self.target_type = 0

        if self.target_type == 6:
            pass
        elif self.target_type == 5:
            pass
        elif self.target_type == 4:
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
                if env == Environment.ORE_TITANIUM:
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
                                        has_space = c.get_tile_env(nxt) != Environment.WALL
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
                        building_id = c.get_tile_building_id(pos)
                        e_type = c.get_entity_type(building_id)
                        if e_type == EntityType.BARRIER:
                            if self.is_troll or c.get_team(building_id) != my_team:
                                continue
                        elif e_type == EntityType.HARVESTER:
                            if self.is_troll:
                                continue

                        if c.get_tile_builder_bot_id(pos) is not None:
                            continue

                        dist = my_pos.distance_squared(pos)
                        if self.target_type == 2:
                            if dist >= self.target_dist:
                                continue
                        self.target = pos
                        self.target_type = 2
                        self.target_dist = dist
                        self.conveyor_manager = None

                if c.get_current_round() >= 200 and pos.distance_squared(my_pos) <= 2 and pos.distance_squared(self.home) <= 13:
                    building_id = c.get_tile_building_id(pos)
                    if c.get_entity_type(building_id) in MONOCHILD_CONVEYOR:
                        d: Direction = c.get_direction(building_id)
                        count = 0
                        for e in CARDINAL:
                            cur = pos.add(e)
                            if 0 <= cur.x < W and 0 <= cur.y < H:
                                building_id = c.get_tile_building_id(cur)
                                e_type = c.get_entity_type(building_id)
                                if e_type == EntityType.SPLITTER:
                                    count += 1
                                elif e_type in MONOCHILD_CONVEYOR and c.get_direction(building_id) == e.opposite():
                                    count += 1
                        if count == 1:
                            for d in (d.rotate_left().rotate_left(), d.rotate_right().rotate_right()):
                                cur = pos.add(d)
                                if cur.distance_squared(self.home) > 8:
                                    continue
                                if not (0 <= cur.x < W and 0 <= cur.y < H):
                                    continue
                                building_id = c.get_tile_building_id(cur)
                                if building_id is not None and c.get_entity_type(building_id) not in UNIMPORTANT:
                                    break
                                cur = cur.add(d)
                                if cur.distance_squared(self.home) > 8:
                                    continue
                                if not (0 <= cur.x < W and 0 <= cur.y < H):
                                    continue
                                building_id = c.get_tile_building_id(cur)
                                if building_id is not None and c.get_entity_type(building_id) not in UNIMPORTANT:
                                    break
                                for e in Direction:
                                    adj = cur.add(e)
                                    if 0 <= adj.x < W and 0 <= adj.y < H:
                                        building_id = c.get_tile_building_id(adj)
                                        if building_id is not None and c.get_entity_type(building_id) not in CHAMBER_WALL:
                                            break
                                else:
                                    self.target = pos
                                    self.sub_target = pos.add(d)
                                    self.target_type = 7

                building_id = c.get_tile_building_id(pos)
                if c.get_entity_type(building_id) in CONVEYOR_VARIANT:
                    if c.get_team(building_id) != my_team:
                        if c.get_hp(building_id) < c.get_max_hp(building_id):
                            self.target = pos
                            self.target_type = 9
                # if pos.distance_squared(my_pos) <= 10 and needs_repair(pos):
                #     # Need to repair!
                #     print("rep", pos)
                #     self.target = pos
                #     self.target_type = 5
                #     self.conveyor_manager = None
                #     break

    def run(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position()
        my_team = c.get_team()
        W, H = c.get_map_width(), c.get_map_height()

        if self.home is None:
            self.birth = c.get_current_round()
            self.home = c.get_position(c.get_tile_building_id(my_pos))
            self.movement = Movement()
            self.tile_manager = TileManager(c, self.home)
            self.bfs = Bfs(self.home, self.tile_manager)
            self.nav = AStarNav(self.tile_manager, self.bfs)
            self.prev_resources = c.get_global_resources()[0]

            # if self.birth >= 100:
            #     if not FoundryManager.check_foundry(c):
            #         self.foundry_manager = FoundryManager(self.home, self.birth + 25)
            #         self.target_type = 6

        self.is_troll = 3 <= self.birth <= 4 and c.get_current_round() <= 300
        delta = c.get_global_resources()[0] - self.prev_resources
        self.has_econ |= delta > 0
        self.has_harvester |= delta <= -0.8 * c.get_harvester_cost()[0]

        if self.target_type == 1:
            if my_pos.distance_squared(self.target) <= 4 or c.get_current_round() > self.expiry:
                self.target_type = 0
        elif self.target_type == 2:
            if c.is_in_vision(self.target):
                bb_id = c.get_tile_builder_bot_id(self.target)
                if bb_id is not None and bb_id != my_id:
                    self.target_type = 0
                else:
                    if self.is_troll:
                        building_id = c.get_tile_building_id(self.target)
                        e_type = c.get_entity_type(building_id)
                        if c.get_team(building_id) == my_team:
                            if e_type == EntityType.BARRIER or e_type == EntityType.HARVESTER:
                                self.target_type = 0
                        else:
                            if e_type not in DESTROY_ENEMY:
                                self.target_type = 0
        elif self.target_type == 3:
            if self.conveyor_manager.done:
                self.target_type = 0

        self.tile_manager.sense(c, self.home)
        self.bfs.update(c, self.conveyor_manager)

        if self.target_type == 2:
            if not self.tile_manager.build_harvester[self.target.y][self.target.x]:
                self.target_type = 0

            if self.target_type:
                dist = my_pos.distance_squared(self.target)
                self.target_dist = min(self.target_dist, dist)

                if not self.is_troll:
                    if dist <= 2:
                        self.conveyor_manager = ConveyorManager(c, self.tile_manager, self.target, self.home, self.nav)
                        if self.conveyor_manager.path:
                            self.target = self.home
                            self.target_type = 3
                            self.target_dist = my_pos.distance_squared(self.target)
                        else:
                            self.tile_manager.ban_harvester[self.target.y][self.target.x] = True
                            self.target_type = 0

        self.sense(c)
        self.movement.upd(c)

        if self.target_type == 1:
            if not self.tile_manager.pass_grid[self.target.y][self.target.x]:
                self.target_type = 0

        core: Position = self.home
        if not c.is_in_vision(core):
            core = core.add(self.home.direction_to(my_pos))

        heal_core: bool = False
        if c.is_in_vision(core):
            building_id = c.get_tile_building_id(core)
            if c.get_hp(building_id) < c.get_max_hp(building_id):
                pass_ = (self.tile_manager.pass_ | self.tile_manager.buildable) & ~self.tile_manager.ally & ~self.tile_manager.enemy
                if core == self.home:
                    d = self.bfs.bfs_adj(core.x - my_pos.x, core.y - my_pos.y, pass_)
                else:
                    d = self.bfs.bfs_to_pos(core.x - my_pos.x, core.y - my_pos.y, pass_)
                if d is not None:
                    heal_core = True
                    if d != Direction.CENTRE and self.movement.can_move(d):
                        self.movement.move(d)

        if ((c.get_hp(my_id) < c.get_max_hp(my_id) and self.target_type != 4) or heal_core) and c.can_heal(my_pos):
            c.heal(my_pos)
            self.movement.act(c)

        if heal_core:
            return

        if self.target_type == 0:
            for _ in range(10):
                self.target = Position(random.randint(0, c.get_map_width() - 1), random.randint(0, c.get_map_height() - 1))
                if self.tile_manager.pass_grid[self.target.y][self.target.x]:
                    self.target_type = 1
                    self.expiry = c.get_current_round() + 260
                    break

        if self.target_type == 1:
            c.draw_indicator_line(my_pos, self.target, 255, 0, 0)
            self.nav.move(c, self.target, self.movement)
        elif self.target_type == 2:
            c.draw_indicator_line(my_pos, self.target, 0, 255, 0)
            dist = my_pos.distance_squared(self.target)
            if self.is_troll:
                if dist <= 20:
                    building_id = c.get_tile_building_id(self.target)
                    if c.get_team(building_id) != my_team and c.get_entity_type(building_id) != EntityType.MARKER:
                        self.nav.move(c, self.target, self.movement)
                        if c.can_fire(self.target):
                            c.fire(self.target)
                            building_id = c.get_tile_building_id(self.target)

                if not dist:
                    if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_barrier_cost()[0]:
                        if c.get_team(building_id) == my_team:
                            for d in DIRECTIONS:
                                if c.can_move(d):
                                    c.move(d)
                                    if c.can_destroy(self.target):
                                        c.destroy(self.target)
                elif dist > 2:
                    self.nav.move(c, self.target, self.movement)

                if c.can_build_barrier(self.target):
                    c.build_barrier(self.target)
                    self.target_type = 0
            else:
                if dist > 2:
                    self.nav.move(c, self.target, self.movement)
        elif self.target_type == 3:
            self.conveyor_manager.update(c, self.movement, self.tile_manager, self.bfs)
            if not self.conveyor_manager.index:
                self.target_type = 0
        elif self.target_type == 4:
            sentinel_targets: list[Position] = []
            for d in CARDINAL:
                nxt = self.target.add(d)
                if 0 <= nxt.x < W and 0 <= nxt.y < H:
                    if c.is_in_vision(nxt):
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
                            nxt = target.add(d.rotate_left())
                            if 0 <= nxt.x < W and 0 <= nxt.y < H:
                                building_id = c.get_tile_building_id(nxt)
                                if c.get_team(building_id) != my_team:
                                    d = d.rotate_left()
                                else:
                                    d = d.rotate_right()
                            else:
                                d = d.rotate_right()
                            c.build_sentinel(target, d)
                            self.target_type = 0
                            break
        elif self.target_type == 5:
            if self.conveyor_manager is None:
                if my_pos.distance_squared(self.target) <= 2:
                    self.conveyor_manager = ConveyorManager(c, self.tile_manager, self.target, self.home)
                    self.conveyor_manager.index -= 1
                else:
                    self.nav.move(c, self.target, self.movement)
                c.draw_indicator_line(my_pos, self.target, 128, 0, 255)

            if self.conveyor_manager is not None:
                self.conveyor_manager.update(c, self.movement, self.tile_manager, self.bfs, True)

                if self.conveyor_manager.done:
                    self.target_type = 0
        elif self.target_type == 6:
            self.foundry_manager.update(c, self.movement, self.tile_manager, self.bfs)

            if self.foundry_manager.check_foundry(c) or c.get_current_round() >= self.foundry_manager.expiry and self.foundry_manager.target is None:
                self.target_type = 0
        elif self.target_type == 7:
            dist = my_pos.distance_squared(self.target)
            if dist > 8:
                self.nav.move(c, self.target, self.movement)
            else:
                building_id = c.get_tile_building_id(self.target)
                if c.get_entity_type(building_id) == EntityType.SPLITTER:
                    building_id = c.get_tile_building_id(self.sub_target)
                    if c.get_entity_type(building_id) == EntityType.GUNNER:
                        target = self.sub_target.add(self.target.direction_to(self.sub_target))
                        if my_pos != target:
                            self.nav.move(c, target, self.movement)
                            my_pos = c.get_position()

                        if my_pos == target:
                            for d in DIRECTIONS:
                                cur = target.add(d)
                                if 0 <= cur.x < W and 0 <= cur.y < H:
                                    building_id = c.get_tile_building_id(cur)
                                    if building_id is None or c.get_entity_type(building_id) in UNIMPORTANT:
                                        if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_barrier_cost()[0]:
                                            if c.can_destroy(cur):
                                                c.destroy(cur)
                                            c.build_barrier(cur)
                                        else:
                                            break
                            else:
                                self.target_type = 8
                                self.sub_target = target
                                for d in DIRECTIONS:
                                    cur = target.add(d)
                                    building_id = c.get_tile_building_id(cur)
                                    if c.get_entity_type(building_id) == EntityType.CORE:
                                        self.target = cur
                                        break
                    else:
                        dist = my_pos.distance_squared(self.sub_target)
                        if dist > 2:
                            self.nav.move(c, self.sub_target, self.movement)
                        else:
                            if not dist:
                                for d in DIRECTIONS:
                                    if c.can_move(d):
                                        self.movement.move(d)
                                        my_pos = c.get_position()
                                        dist = my_pos.distance_squared(self.sub_target)
                                        break
                            if dist:
                                if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_gunner_cost()[0]:
                                    d: Direction = self.target.direction_to(self.sub_target)
                                    if c.can_destroy(self.sub_target):
                                        c.destroy(self.sub_target)
                                    c.build_gunner(self.sub_target, d)
                else:
                    if dist <= 2:
                        if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_splitter_cost()[0]:
                            d: Direction = c.get_direction(building_id)
                            if c.can_destroy(self.target):
                                c.destroy(self.target)
                            c.build_splitter(self.target, d)
                    else:
                        self.nav.move(c, self.target, self.movement)
        elif self.target_type == 8:
            if my_pos != self.target:
                self.nav.move(c, self.target, self.movement)
            if my_pos.distance_squared(self.sub_target) <= 2:
                building_id = c.get_tile_building_id(self.sub_target)
                if c.get_entity_type(building_id) != EntityType.ROAD:
                    if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_road_cost()[0]:
                        if c.can_destroy(self.sub_target):
                            c.destroy(self.sub_target)
                        c.build_road(self.sub_target)
        elif self.target_type == 9:
            if c.is_in_vision(self.target):
                building_id = c.get_tile_building_id(self.target)
                if c.get_hp(building_id) == c.get_max_hp(building_id):
                    self.target_type = 0
                else:
                    if c.can_heal(self.target):
                        c.heal(self.target)
                    self.nav.move(c, self.target, self.movement)
                    if c.can_heal(self.target):
                        c.heal(self.target)
            else:
                self.nav.move(c, self.target, self.movement)
        if self.target_type != 3:
            my_pos = c.get_position()
            if not c.get_move_cooldown():
                for d in DIRECTIONS:
                    pos: Position = my_pos.add(d)
                    x, y = pos
                    if 0 <= x < W and 0 <= y < H:
                        bbot_id = c.get_tile_builder_bot_id(pos)
                        if bbot_id is not None and c.get_team(bbot_id) == my_team:
                            building_id = c.get_tile_building_id(pos)
                            if c.get_entity_type(building_id) in CONVEYOR_VARIANT:
                                d: Direction = self.bfs.get_move(self.tile_manager.pass_ & ~self.tile_manager.ally & ~self.tile_manager.enemy)
                                if d != Direction.CENTRE:
                                    self.movement.move(d)
                                break

        self.prev_resources = c.get_global_resources()[0]
