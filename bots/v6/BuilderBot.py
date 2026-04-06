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
import consts as C
import utils as U


class BuilderBot(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)
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
        self.ores: set[Position] = set()
        self.is_healer: bool = False

    def sense(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        x, y = my_pos

        def needs_repair(pos: Position, trustworthy: bool = False) -> bool:
            if c.is_in_vision(pos):
                building_id = c.get_tile_building_id(pos)
                if c.get_team(building_id) == my_team:
                    e_type = c.get_entity_type(building_id)
                    if e_type in C.CONVEYOR:
                        if c.get_stored_resource(building_id) is not None:
                            d: Direction = c.get_direction(building_id)
                            nxt = pos.add(d)
                            if c.is_in_vision(nxt):
                                building_id = c.get_tile_building_id(nxt)
                                if building_id is not None and c.get_team(building_id) == my_team and c.get_entity_type(building_id) not in C.UNIMPORTANT:
                                    return False
                                if not trustworthy:
                                    for e in Direction:
                                        nxt = pos.add(e)
                                        if U.on_the_map(nxt):
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
                    for d in C.CARDINAL:
                        nxt = self.target.add(d)
                        if U.on_the_map(nxt):
                            building_id = c.get_tile_building_id(nxt)
                            if building_id is None:
                                has_space = c.get_tile_env(nxt) != Environment.WALL
                            elif c.get_team(building_id) == my_team:
                                e_type = c.get_entity_type(building_id)
                                if e_type == EntityType.SENTINEL:
                                    has_enemy = False
                                    break
                                else:
                                    has_space |= e_type in C.UNIMPORTANT
                            else:
                                has_enemy |= c.get_entity_type(building_id) != EntityType.MARKER

                    if has_space and has_enemy:
                        self.target_type = 4
        elif self.target_type == 5:
            if self.conveyor_manager is None and not needs_repair(self.target, True):
                self.target_type = 0

        if self.target_type <= 2 and not self.is_healer:
            for pos in c.get_nearby_tiles(2):
                if c.get_tile_env(pos) == Environment.ORE_TITANIUM and self.tile_manager.build_harvester[pos.y][pos.x]:
                    for d in Direction:
                        cur = pos.add(d)
                        if U.is_visible(cur):
                            bb_id = c.get_tile_builder_bot_id(cur)
                            if bb_id is not None and c.get_team(bb_id) == my_team and bb_id != my_id:
                                break
                    else:
                        self.target = pos
                        self.conveyor_manager = ConveyorManager(self.nav, self.home)
                        self.conveyor_manager.generate_path(c, self.tile_manager, self.target)
                        self.target_type = 3
                        break

        if self.target_type == 6:
            pass
        elif self.target_type == 5:
            pass
        elif self.target_type == 4:
            pass
        elif self.target_type == 3:
            if self.conveyor_manager.path:
                retargets: list[Position] = []
                reroute: bool = False
                path_index = self.conveyor_manager.path_index
                for pos in c.get_nearby_tiles():
                    building_id = c.get_tile_building_id(pos)
                    if c.get_entity_type(building_id) in C.MONOCHILD_CONVEYOR and c.get_team(building_id) == my_team:
                        xi, yi = pos
                        cur_index = path_index[yi][xi]
                        if cur_index >= self.conveyor_manager.index:
                            if cur_index == self.conveyor_manager.index:
                                self.conveyor_manager.avoid_joining = False
                            reroute |= cur_index < 1000000
                            good = True
                            cur = pos
                            for _ in range(10):
                                building_id = c.get_tile_building_id(cur)
                                if building_id is None or c.get_team(building_id) != my_team:
                                    good = False
                                    break
                                e_type = c.get_entity_type(building_id)
                                if e_type in C.CONVEYOR:
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

                self.conveyor_manager.retarget(c, retargets, self.tile_manager, reroute)
        else:
            for pos in c.get_nearby_tiles():
                env: Environment = c.get_tile_env(pos)
                if env == Environment.ORE_TITANIUM and not self.is_healer:
                    building_id = c.get_tile_building_id(pos)
                    if c.get_entity_type(building_id) == EntityType.HARVESTER:
                        dist = my_pos.distance_squared(pos)
                        xi, yi = pos
                        if dist <= 13 and self.bfs.can_reach_adj(xi - x, yi - y):
                            has_space, has_enemy = False, False
                            for d in C.CARDINAL:
                                nxt = pos.add(d)
                                if U.on_the_map(nxt):
                                    building_id = c.get_tile_building_id(nxt)
                                    if building_id is None:
                                        has_space = c.get_tile_env(nxt) != Environment.WALL
                                    elif c.get_team(building_id) == my_team:
                                        e_type = c.get_entity_type(building_id)
                                        if e_type == EntityType.SENTINEL:
                                            has_enemy = False
                                            break
                                        else:
                                            has_space |= e_type in C.UNIMPORTANT
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
                                self.ores.discard(pos)
                                continue
                        elif e_type == EntityType.HARVESTER:
                            if self.is_troll:
                                self.ores.discard(pos)
                                continue

                        if c.get_tile_builder_bot_id(pos) is not None:
                            self.ores.discard(pos)
                            continue

                        self.ores.add(pos)
                        self.target_type = 2
                    else:
                        self.ores.discard(pos)

                building_id = c.get_tile_building_id(pos)
                if c.get_entity_type(building_id) in C.CONVEYOR_VARIANT:
                    if c.get_team(building_id) == my_team:
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

            if self.target_type == 2:
                rem: list[Position] = []
                for target in self.ores:
                    if c.is_in_vision(target):
                        for d in Direction:
                            pos = target.add(d)
                            if U.is_visible(pos):
                                bb_id = c.get_tile_builder_bot_id(pos)
                                if bb_id is not None and c.get_team(bb_id) == my_team and bb_id != my_id:
                                    rem.append(target)
                                    break
                for pos in rem:
                    self.ores.remove(pos)
                if self.ores:
                    closest_dist: int = 10000
                    self.target = None
                    for pos in self.ores:
                        dist = my_pos.distance_squared(pos)
                        if dist < closest_dist:
                            closest_dist = dist
                            self.target = pos
                else:
                    self.target_type = 0

    def run(self, c: Controller):
        super().run(c)
        my_id = c.get_id()
        my_pos = c.get_position()
        my_team = c.get_team()

        if self.home is None:
            self.birth = c.get_current_round()
            self.home = c.get_position(c.get_tile_building_id(my_pos))
            self.movement = Movement()
            self.tile_manager = TileManager(self.home)
            self.bfs = Bfs(self.home, self.tile_manager)
            self.nav = AStarNav(self.tile_manager, self.bfs)
            self.prev_resources = c.get_global_resources()[0]
            self.is_healer = self.birth >= 4

            # if self.birth >= 100:
            #     if not FoundryManager.check_foundry(c):
            #         self.foundry_manager = FoundryManager(self.home, self.birth + 25)
            #         self.target_type = 6

        # self.is_troll = 3 <= self.birth <= 4 and c.get_current_round() <= 300

        if self.target_type == 1:
            if my_pos.distance_squared(self.target) <= 4 or c.get_current_round() > self.expiry:
                self.target_type = 0
        elif self.target_type == 3:
            if self.conveyor_manager.done:
                self.target_type = 0

        self.tile_manager.sense(c, self.home)
        self.bfs.update(c, self.conveyor_manager)

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
            if self.is_healer and self.home.distance_squared(my_pos) > 30:
                self.target_type = 1
                self.target = self.home
            else:
                for _ in range(10):
                    self.target = Position(random.randint(0, c.get_map_width() - 1), random.randint(0, c.get_map_height() - 1))
                    if self.target != my_pos and self.tile_manager.pass_grid[self.target.y][self.target.x]:
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
                            for d in C.DIRECTIONS:
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
                    self.nav.multimove(c, list(self.ores), self.movement)
        elif self.target_type == 3:
            if not self.conveyor_manager.path:
                if c.get_cpu_time_elapsed() <= 600:
                    self.conveyor_manager.generate_path(c, self.tile_manager, self.target, False)
                    if not self.conveyor_manager.path:
                        self.tile_manager.ban_harvester[self.target.y][self.target.x] = True
                        self.target_type = 0

            if self.conveyor_manager.path:
                self.conveyor_manager.update(c, self.movement, self.tile_manager, self.bfs, False)
                if not self.conveyor_manager.index:
                    self.target_type = 0
        elif self.target_type == 4:
            sentinel_targets: list[Position] = []
            for d in C.CARDINAL:
                nxt = self.target.add(d)
                if U.on_the_map(nxt):
                    if c.is_in_vision(nxt):
                        building_id = c.get_tile_building_id(nxt)
                        if building_id is None or c.get_team(building_id) == my_team and c.get_entity_type(building_id) in C.UNIMPORTANT:
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
                            if U.on_the_map(nxt):
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
                    self.conveyor_manager = ConveyorManager(self.nav, self.home)
                    self.conveyor_manager.generate_path(c, self.tile_manager, self.target)
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
                for d in C.DIRECTIONS:
                    pos: Position = my_pos.add(d)
                    if U.on_the_map(pos):
                        bbot_id = c.get_tile_builder_bot_id(pos)
                        if bbot_id is not None and c.get_team(bbot_id) == my_team:
                            building_id = c.get_tile_building_id(pos)
                            if c.get_entity_type(building_id) in C.CONVEYOR_VARIANT:
                                d: Direction = self.bfs.get_move(self.tile_manager.pass_ & ~self.tile_manager.ally & ~self.tile_manager.enemy)
                                if d != Direction.CENTRE:
                                    self.movement.move(d)
                                break

        self.prev_resources = c.get_global_resources()[0]
