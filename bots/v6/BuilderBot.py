import random
from cambc import *
from Unit import Unit
from Movement import Movement
from Nav import Nav
from ConveyorManager import ConveyorManager
from TileManager import TileManager
from Bfs import Bfs
from FoundryManager import FoundryManager
from AStarNav import AStarNav
import consts as C
import utils as U
from BfsNav import BfsNav
from Wander import Wander
from CommunicationManager import CommunicationManager


class BuilderBot(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)
        self.birth = c.get_current_round()
        self.home = c.get_position(c.get_tile_building_id(c.get_position()))
        self.tile_manager = TileManager(self.home)
        self.bfs = Bfs(self.home, self.tile_manager)
        self.nav: Nav = AStarNav(self.tile_manager, self.bfs)
        self.bfs_nav: BfsNav = BfsNav(self.home, self.tile_manager)
        self.prev_resources = c.get_global_resources()[0]
        self.is_healer = self.birth >= 4
        self.movement: Movement = Movement()
        self.wander: Wander = Wander(self.nav, self.movement)
        self.target: Position | None = None
        self.sub_target: Position | None = None
        self.target_type: int = 0  # 0: nothing, 1: explore, 2: go to ore, 3: build conveyor home, 4: destroy enemy conveyors, 5: repair conveyor
        self.target_dist: int = 0
        self.conveyor_manager: ConveyorManager | None = None
        self.expiry: int = 0
        self.foundry_manager: FoundryManager | None = None
        self.is_troll: bool = False
        self.has_econ: bool = False
        self.has_harvester: bool = False
        self.ores: set[Position] = set()
        self.routed_titanium: bool = False
        self.routed_axionite: bool = False
        self.is_axionite: bool = False
        self.communication_manager: CommunicationManager = CommunicationManager()

        # if self.birth >= 100:
        #     if not FoundryManager.check_foundry(c):
        #         self.foundry_manager = FoundryManager(self.home, self.birth + 25)
        #         self.target_type = 6

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
        elif self.target_type == 7:
            if c.is_in_vision(self.target):
                if c.get_entity_type(c.get_tile_building_id(self.target)) in C.TURRET:
                    self.target_type = 0

        if self.target_type <= 2 and not self.is_healer:
            e_type = Environment.ORE_AXIONITE if self.is_axionite else Environment.ORE_TITANIUM
            for pos in c.get_nearby_tiles(2):
                if c.get_tile_env(pos) == e_type and self.tile_manager.build_harvester[pos.y][pos.x]:
                    for d in Direction:
                        cur = pos.add(d)
                        if U.is_visible(cur):
                            bb_id = c.get_tile_builder_bot_id(cur)
                            if bb_id is not None and c.get_team(bb_id) == my_team and bb_id != my_id:
                                break
                    else:
                        enemy_core = self.tile_manager.enemy_core
                        if enemy_core is not None and pos.distance_squared(enemy_core) <= pos.distance_squared(self.home):
                            # Attack!
                            self.conveyor_manager = ConveyorManager(self.nav, enemy_core)
                        else:
                            self.conveyor_manager = ConveyorManager(self.nav, self.home)
                        if self.is_axionite:
                            self.conveyor_manager.generate_path(c, self.tile_manager, pos, 2)
                            if not self.conveyor_manager.path:
                                self.tile_manager.ban_harvester[pos.y][pos.x] = True
                                continue
                        else:
                            self.conveyor_manager.generate_path(c, self.tile_manager, pos)
                        self.target = pos
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
                stuck: bool = False
                path_index = self.conveyor_manager.path_index
                for pos in c.get_nearby_tiles():
                    building_id = c.get_tile_building_id(pos)
                    if c.get_entity_type(building_id) in C.MONOCHILD_CONVEYOR and c.get_team(building_id) == my_team:
                        xi, yi = pos
                        cur_index = path_index[yi][xi]
                        if cur_index >= self.conveyor_manager.index:
                            if cur_index == self.conveyor_manager.index:
                                self.conveyor_manager.avoid_joining = False
                            stuck |= cur_index < 1000000
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

                self.conveyor_manager.retarget(c, retargets, self.tile_manager, stuck)
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

                    if self.tile_manager.build_harvester[pos.y][pos.x]:
                        if self.target_type <= 2:
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

                            # TODO: also when >2
                            self.ores.add(pos)
                            self.target_type = 2
                    else:
                        self.ores.discard(pos)

                building_id = c.get_tile_building_id(pos)
                e_type = c.get_entity_type(building_id)
                if c.get_team(building_id) == my_team:
                    if e_type not in C.UNIMPORTANT:
                        if c.get_hp(building_id) < c.get_max_hp(building_id):
                            self.target = pos
                            self.target_type = 9
                            break
                elif e_type in C.DANGEROUS:
                    x, y = pos
                    if not self.tile_manager.gunner_covered_grid[y][x]:
                        for d in C.CARDINAL:
                            nxt: Position = pos.add(d)
                            if U.is_visible(nxt):
                                building_id = c.get_tile_building_id(nxt)
                                if c.get_team(building_id) == my_team:
                                    e_type = c.get_entity_type(building_id)
                                    if e_type == EntityType.BRIDGE:
                                        if pos != c.get_bridge_target(building_id):
                                            continue
                                    elif e_type in C.CONVEYOR_VARIANT:
                                        if d != c.get_direction(building_id).opposite():
                                            continue
                                    else:
                                        continue
                                    self.target = nxt
                                    self.sub_target = pos
                                    self.target_type = 7
                                    break

                        if self.target_type < 7:
                            for d in C.CARDINAL:
                                nxt: Position = pos.add(d)
                                for e in C.CARDINAL:
                                    if e == d.opposite():
                                        continue
                                    adj: Position = nxt.add(e)
                                    if U.is_visible(adj):
                                        building_id = c.get_tile_building_id(adj)
                                        if c.get_team(building_id) == my_team:
                                            e_type = c.get_entity_type(building_id)
                                            if e_type == EntityType.BRIDGE:
                                                if pos != c.get_bridge_target(building_id):
                                                    continue
                                            elif e_type in C.CONVEYOR_VARIANT:
                                                if d != c.get_direction(building_id).opposite():
                                                    continue
                                            else:
                                                continue
                                            self.target = adj
                                            self.sub_target = pos
                                            self.target_type = 7
                                            break
                # if pos.distance_squared(my_pos) <= 10 and needs_repair(pos):
                #     # Need to repair!
                #     print("rep", pos)
                #     self.target = pos
                #     self.target_type = 5
                #     self.conveyor_manager = None
                #     break

            if self.target_type == 2:
                if self.is_axionite:
                    ores: set[Position] = self.tile_manager.axionite_ores
                else:
                    ores: set[Position] = self.ores

                rem: list[Position] = []
                for target in ores:
                    if c.is_in_vision(target):
                        for d in Direction:
                            pos = target.add(d)
                            if U.is_visible(pos):
                                bb_id = c.get_tile_builder_bot_id(pos)
                                if bb_id is not None and c.get_team(bb_id) == my_team and bb_id != my_id:
                                    rem.append(target)
                                    break
                for pos in rem:
                    ores.remove(pos)
                if ores:
                    closest_dist: int = 10000
                    self.target = None
                    for pos in ores:
                        dist = my_pos.distance_squared(pos)
                        if dist < closest_dist:
                            closest_dist = dist
                            self.target = pos
                else:
                    self.target_type = 0

    def run(self, c: Controller):
        super().run(c)
        my_pos = c.get_position()
        my_team = c.get_team()

        self.communication_manager.update(c)

        U.can_afford = lambda building: not c.get_action_cooldown() and c.get_global_resources()[0] >= getattr(c, f"get_{building}_cost")()[0]
        # self.is_troll = 3 <= self.birth <= 4 and c.get_current_round() <= 300

        if self.target_type == 1:
            if my_pos.distance_squared(self.target) <= 4 or c.get_current_round() > self.expiry:
                self.target_type = 0
        elif self.target_type == 3:
            if self.conveyor_manager.done:
                if self.is_axionite:
                    self.routed_axionite = True
                    self.is_axionite = False
                else:
                    self.routed_titanium = True
                self.target_type = 0

        self.tile_manager.sense(c, self.home, self.wander)
        self.bfs.update(c, self.conveyor_manager)

        if self.birth == 1 and self.target_type <= 2:
            if self.tile_manager.axionite_ores and self.routed_titanium and not self.routed_axionite:
                self.target_type = 2
                self.is_axionite = True
            else:
                self.is_axionite = False

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
                        my_pos = c.get_position()

        if heal_core:
            target = self.home.add(self.home.direction_to(my_pos))
            if c.can_heal(target):
                c.heal(target)

            return

        if self.target_type == 0:
            if not self.is_healer:
                for _ in range(10):
                    self.target = Position(random.randint(0, c.get_map_width() - 1), random.randint(0, c.get_map_height() - 1))
                    if self.target != my_pos and self.tile_manager.pass_grid[self.target.y][self.target.x]:
                        self.target_type = 1
                        self.expiry = c.get_current_round() + 260
                        break

        if self.target_type <= 2:
            for pos, info in self.tile_manager.gunners.items():
                if info[1]:
                    if c.can_destroy(pos):
                        c.destroy(pos)

            def try_repair():
                building_grid = self.tile_manager.building_grid
                x, y = my_pos
                if building_grid[y][x] is not None:
                    e_type: EntityType
                    e_type, extra = building_grid[y][x]
                    building_id = c.get_tile_building_id(my_pos)
                    if c.get_team(building_id) != my_team:
                        if c.can_fire(my_pos):
                            c.fire(my_pos)
                    elif c.get_entity_type(building_id) in C.UNIMPORTANT:
                        if U.can_afford(e_type.value):
                            c.destroy(my_pos)

                    if isinstance(extra, Direction):
                        nxt = my_pos.add(extra)
                    else:
                        nxt = extra
                    building_id = c.get_tile_building_id(nxt)
                    if c.get_team(building_id) == my_team or c.get_entity_type(building_id) in C.UNIMPORTANT:
                        if c.can_build(e_type, my_pos, extra):
                            c.build(e_type, my_pos, extra)
                            self.tile_manager.has_building_bitset[y] |= 1 << x
                            self.movement.act(c)
                            return

                for d in C.DIRECTIONS:
                    pos = my_pos.add(d)
                    if U.on_the_map(pos):
                        x, y = pos
                        if building_grid[y][x] is not None:
                            e_type, extra = building_grid[y][x]
                            building_id = c.get_tile_building_id(pos)
                            if c.get_team(building_id) == my_team and c.get_entity_type(building_id) in C.UNIMPORTANT:
                                if U.can_afford(e_type.value):
                                    c.destroy(pos)

                            if isinstance(extra, Direction):
                                nxt = pos.add(extra)
                            else:
                                nxt = extra
                            building_id = c.get_tile_building_id(nxt)
                            if c.get_team(building_id) == my_team or c.get_entity_type(building_id) in C.UNIMPORTANT:
                                if c.can_build(e_type, pos, extra):
                                    c.build(e_type, pos, extra)
                                    self.tile_manager.has_building_bitset[y] |= 1 << x
                                    self.movement.act(c)
                                    return

            try_repair()
            had_building: int = self.tile_manager["had_building"]
            has_building: int = self.tile_manager["has_building"]
            buildable: int = self.tile_manager["buildable"]
            repair: int = (had_building ^ has_building) & buildable
            if repair:
                self.bfs_nav.multimove(c, repair, self.movement)
                my_pos = c.get_position()
                try_repair()
                self.target_type = ~self.target_type

        if self.target_type < 0:
            self.target_type = ~self.target_type
        elif self.target_type == 0:
            self.wander.update(c)
        elif self.target_type == 1:
            c.draw_indicator_line(my_pos, self.target, 255, 0, 0)
            self.nav.move(c, self.target, self.movement)
        elif self.target_type == 2:
            if self.is_axionite:
                if my_pos.distance_squared(self.target) > 2:
                    self.nav.multimove(c, list(self.tile_manager.axionite_ores), self.movement)
            else:
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
                    self.conveyor_manager.generate_path(c, self.tile_manager, self.target, 1)
                    if not self.conveyor_manager.path:
                        self.tile_manager.ban_harvester[self.target.y][self.target.x] = True
                        self.target_type = 0

            if self.conveyor_manager.path:
                self.conveyor_manager.update(c, self.movement, self.tile_manager, self.bfs, False)
                if not self.conveyor_manager.index:
                    self.tile_manager.ban_harvester[self.target.y][self.target.x] = True
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
                    if self.is_axionite:
                        self.routed_axionite = True
                        self.is_axionite = False
                    else:
                        self.routed_titanium = True
                    self.target_type = 0
        elif self.target_type == 6:
            self.foundry_manager.update(c, self.movement, self.tile_manager, self.bfs)

            if self.foundry_manager.check_foundry(c) or c.get_current_round() >= self.foundry_manager.expiry and self.foundry_manager.target is None:
                self.target_type = 0
        elif self.target_type == 7:
            c.draw_indicator_line(my_pos, self.target, 128, 255, 0)
            dist = my_pos.distance_squared(self.target)
            if c.can_destroy(self.target):
                c.destroy(self.target)

            if U.can_afford("gunner"):
                if not dist:
                    if not c.get_action_cooldown():
                        for d in C.DIRECTIONS:
                            if c.can_move(d):
                                self.movement.move(d)
                                my_pos = c.get_position()
                                dist = my_pos.distance_squared(my_pos)
                                break

                if 1 <= dist <= 2:
                    d: Direction = self.target.direction_to(self.sub_target)
                    if c.can_build_gunner(self.target, d):
                        c.build_gunner(self.target, d)
                        self.target_type = 0

            if self.target_type and dist:
                self.nav.move(c, self.target, self.movement)
        elif self.target_type == 9:
            self.movement.enrich(c)
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

        my_pos = c.get_position()
        if not c.get_action_cooldown():
            if c.get_hp() < c.get_max_hp() and self.target_type != 4 and c.can_heal(my_pos):
                c.heal(my_pos)
                self.movement.act(c)

        if self.target_type != 3 and not c.get_action_cooldown():
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

        if self.tile_manager.enemy_core is not None:
            x, y = self.tile_manager.enemy_core
            self.communication_manager.mark(x << 6 | y)

        self.prev_resources = c.get_global_resources()[0]
