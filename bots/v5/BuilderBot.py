import random
from lib2to3.pgen2.literals import simple_escapes

from cambc import *
from click import launch

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
        self.target_health: int = 0
        self.conveyor_manager: ConveyorManager | None = None
        self.expiry: int = 0
        self.bfs: Bfs | None = None
        self.foundry_manager: FoundryManager | None = None
        self.is_attacker: bool = False
        self.has_econ: bool = False
        self.prev_resources: int = 1000
        self.has_harvester: bool = False
        self.prev_pos: Position | None = None

    def sense(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)
        x, y = my_pos

        if self.is_attacker:
            if self.target_type == 4:
                if c.is_in_vision(self.target):
                    bb_id = c.get_tile_builder_bot_id(self.target)
                    if bb_id is not None and bb_id != my_id:
                        self.target_type = 0

            for pos in c.get_nearby_tiles():
                building_id = c.get_tile_building_id(pos)
                e_type = c.get_entity_type(building_id)
                if c.get_team(building_id) != my_team:
                    candidates = []
                    if e_type == EntityType.HARVESTER:
                        candidates = [pos.add(d) for d in C.CARDINAL]
                    elif e_type in C.CONVEYOR:
                        candidates = [pos.add(c.get_direction(building_id))]
                    elif e_type == EntityType.BRIDGE:
                        candidates = [c.get_bridge_target(building_id)]
                    for nxt in candidates:
                        if U.is_visible(nxt):
                            building_id = c.get_tile_building_id(nxt)
                            if c.get_team(building_id) == my_team or c.get_entity_type(building_id) == EntityType.MARKER:
                                dist = my_pos.distance_squared(pos)
                                if self.target_type == 5:
                                    if dist < self.target_dist:
                                        self.target = nxt
                                        self.target_dist = dist
                                        continue
                                else:
                                    self.target_type = 5
                                    self.target = nxt
                                    self.target_dist = dist

                    if e_type in C.CONVEYOR_VARIANT and self.target_type <= 4:
                        bb_id = c.get_tile_builder_bot_id(pos)
                        if bb_id is not None and bb_id != my_id:
                            continue

                        health = c.get_hp(building_id)
                        dist = my_pos.distance_squared(pos)
                        if self.target_type == 4:
                            if health < self.target_health:
                                self.target = pos
                                self.target_health = health
                                self.target_dist = dist
                            elif health == self.target_health:
                                if dist < self.target_dist:
                                    self.target = pos
                                    self.target_dist = dist
                        else:
                            self.target_type = 4
                            self.target = pos
                            self.target_dist = dist
                            self.target_health = health
        else:
            if self.target_type <= 2:
                for pos in c.get_nearby_tiles():
                    env: Environment = c.get_tile_env(pos)
                    if env == Environment.ORE_TITANIUM and not self.is_attacker:
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
                                if c.get_team(building_id) != my_team:
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

                    building_id = c.get_tile_building_id(pos)
                    if c.get_entity_type(building_id) in C.CONVEYOR_VARIANT:
                        if c.get_team(building_id) == my_team:
                            if c.get_hp(building_id) < c.get_max_hp(building_id):
                                self.target = pos
                                self.target_type = 9

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
            self.is_attacker = self.birth >= 2

            launched: bool = False
        else:
            launched: bool = my_pos != self.prev_pos

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
                self.is_attacker = True
                self.target_type = 0

        self.tile_manager.sense(c, self.home)
        self.bfs.update(c, self.conveyor_manager)

        if self.target_type == 2:
            if not self.tile_manager.build_harvester[self.target.y][self.target.x]:
                self.target_type = 0

            if self.target_type:
                dist = my_pos.distance_squared(self.target)
                self.target_dist = min(self.target_dist, dist)

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

        building_id = c.get_tile_building_id(my_pos)
        if c.get_team(building_id) != my_team and c.get_entity_type(building_id) in C.CONVEYOR_VARIANT:
            if c.can_fire(my_pos):
                c.fire(my_pos)
                self.movement.act(c)

            if self.target_type == 4:
                building_id = c.get_tile_building_id(my_pos)
                if building_id is not None:
                    health: int = c.get_hp(building_id)
                    if health <= self.target_health:
                        self.target = my_pos
                        self.target_health = health

        if self.target_type == 0:
            for _ in range(10):
                self.target = Position(random.randint(0, c.get_map_width() - 1), random.randint(0, c.get_map_height() - 1))
                if self.target != my_pos and self.tile_manager.pass_grid[self.target.y][self.target.x]:
                    self.target_type = 1
                    self.expiry = c.get_current_round() + 260
                    break

        # print(self.target_type, self.target)
        if self.target_type == 1:
            if self.is_attacker:
                if self.tile_manager.enemy_core is not None:
                    self.target = self.tile_manager.enemy_core

            c.draw_indicator_line(my_pos, self.target, 255, 0, 0)
            if self.is_attacker and self.target == self.tile_manager.enemy_core:
                if my_pos.distance_squared(self.target) <= 8:
                    d: Direction = my_pos.direction_to(self.target)
                    for _ in range(7):
                        if self.movement.can_move(d):
                            self.movement.move(d)
                            break

                        d = d.rotate_left()
                else:
                    self.nav.move(c, self.target, self.movement)
            else:
                self.nav.move(c, self.target, self.movement)
        elif self.target_type == 2:
            c.draw_indicator_line(my_pos, self.target, 0, 255, 0)
            dist = my_pos.distance_squared(self.target)
            if dist > 2:
                self.nav.move(c, self.target, self.movement)
        elif self.target_type == 3:
            self.conveyor_manager.update(c, self.movement, self.tile_manager, self.bfs, False)
            if not self.conveyor_manager.index:
                self.target_type = 0
        elif self.target_type == 4:
            if launched and not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_launcher_cost()[0]:
                best: Position | None = None
                best_score: int = 10000
                for d in C.DIRECTIONS:
                    pos = my_pos.add(d)
                    if U.on_the_map(pos):
                        building_id = c.get_tile_building_id(pos)
                        if building_id is not None:
                            e_type = c.get_entity_type(building_id)
                            if c.get_team(building_id) == my_team:
                                if e_type not in C.UNIMPORTANT:
                                    if e_type == EntityType.LAUNCHER:
                                        break
                                    continue
                            else:
                                if e_type != EntityType.MARKER:
                                    continue

                        score: int = pos.distance_squared(self.target)
                        if score < best_score:
                            best = pos
                            best_score = score
                else:
                    if best is not None:
                        if c.can_destroy(best):
                            c.destroy(best)

                        c.build_launcher(best)
                        self.movement.act(c)

            if c.is_in_vision(self.target):
                building_id = c.get_tile_building_id(self.target)
                if c.get_team(building_id) == my_team or c.get_entity_type(building_id) not in C.CONVEYOR_VARIANT:
                    self.target_type = 0
                else:
                    self.target_health = c.get_hp(building_id)

            if self.target_type:
                if my_pos != self.target:
                    self.nav.move(c, self.target, self.movement)
                    my_pos = c.get_position()

                building_id = c.get_tile_building_id(my_pos)
                if c.get_team(building_id) != my_team and c.get_entity_type(building_id) in C.CONVEYOR_VARIANT:
                    if c.can_fire(my_pos):
                        c.fire(my_pos)

            dist = my_pos.distance_squared(self.target)
            self.target_dist = min(self.target_dist, dist)
        elif self.target_type == 5:
            print(c.get_sentinel_cost())
            dist = my_pos.distance_squared(self.target)
            if not dist:
                if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_sentinel_cost()[0]:
                    for d in C.DIRECTIONS:
                        if c.can_move(d):
                            self.movement.move(d)
                            my_pos = c.get_position()

                            if c.can_destroy(self.target):
                                c.destroy(self.target)
                            if self.tile_manager.enemy_core is None:
                                d: Direction = self.target.direction_to(self.home).opposite()
                            else:
                                d: Direction = self.target.direction_to(self.tile_manager.enemy_core)
                            c.build_sentinel(self.target, d)
                            self.target_type = 0
                            break

                if my_pos == self.target:
                    if c.can_build_road(my_pos):
                        c.build_road(my_pos)
            elif dist <= 2:
                if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_sentinel_cost()[0]:
                    if c.can_destroy(self.target):
                        c.destroy(self.target)
                    if self.tile_manager.enemy_core is None:
                        d: Direction = self.target.direction_to(self.home).opposite()
                    else:
                        d: Direction = self.target.direction_to(self.tile_manager.enemy_core)
                    if c.can_build_sentinel(self.target, d):
                        c.build_sentinel(self.target, d)
                        self.target_type = 0
            else:
                self.nav.move(c, self.target, self.movement)
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

            if not c.get_action_cooldown() and self.tile_manager.enemy_core is not None:
                for d in C.DIRECTIONS:
                    pos: Position = my_pos.add(d)
                    if U.on_the_map(pos):
                        if c.can_place_marker(pos):
                            building_id = c.get_tile_building_id(pos)
                            if building_id is None or c.get_entity_type(building_id) != EntityType.MARKER or c.get_team(building_id) != my_team:
                                x, y = self.tile_manager.enemy_core
                                c.place_marker(pos, x << 6 | y)

        self.prev_resources = c.get_global_resources()[0]
        self.prev_pos = c.get_position()
