import random
from cambc import *
from Unit import Unit
from Movement import Movement
from Nav import Nav
from ConveyorManager import ConveyorManager
from TileManager import TileManager
import consts as C
import utils as U
from BfsNav import BfsNav
from Wander import Wander
from CommunicationManager import CommunicationManager
from ExplorationManager import ExplorationManager
from StalkerManager import StalkerManager
from OffenceManager import OffenceManager


class BuilderBot(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)
        self.birth = c.get_current_round()
        self.home = c.get_position(c.get_tile_building_id(c.get_position()))
        self.tile_manager = TileManager(self.home)
        self.nav: Nav = BfsNav(self.home, self.tile_manager)
        self.prev_resources = c.get_global_resources()[0]
        self.movement: Movement = Movement()
        self.wander: Wander = Wander(self.nav, self.movement)
        self.target: Position | None = None
        self.sub_target: Position | None = None
        self.target_type: int = 0  # 0: nothing, 1: explore, 2: go to ore, 3: build conveyor home, 4: destroy enemy conveyors, 5: repair conveyor
        self.target_dist: int = 0
        self.conveyor_manager: ConveyorManager | None = None
        self.expiry: int = 0
        self.is_troll: bool = False
        self.has_econ: bool = False
        self.has_harvester: bool = False
        self.ores: set[Position] = set()
        self.routed_titanium: bool = False
        self.routed_axionite: bool = False
        self.is_axionite: bool = False
        self.communication_manager: CommunicationManager = CommunicationManager()
        self.must_patrol: bool = True
        self.exploration_manager: ExplorationManager = ExplorationManager()
        self.stalker_manager: StalkerManager = StalkerManager()
        self.must_see_enemy_core: bool = False
        self.offence_manager: OffenceManager | None = None

        target: Position = c.get_position()
        d: Direction = self.home.direction_to(target)
        while U.on_the_map(target):
            target = target.add(d)
        self.exploration_manager.enqueue(target.add(d.opposite()))

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

        if self.target_type == 5:
            if self.conveyor_manager is None and not needs_repair(self.target, True):
                self.target_type = 0
        elif self.target_type == 7:
            if c.is_in_vision(self.target):
                if c.get_entity_type(c.get_tile_building_id(self.target)) in C.TURRET:
                    self.target_type = 0

        targets: dict[int, Position] = self.stalker_manager.targets
        enemy_core: Position | None = self.tile_manager.enemy_core
        for pos in c.get_nearby_tiles():
            env: Environment = c.get_tile_env(pos)
            dist = my_pos.distance_squared(pos)
            if env == Environment.ORE_TITANIUM:
                if self.tile_manager.build_harvester[pos.y][pos.x]:
                    if self.target_type <= 2:
                        b_id = c.get_tile_building_id(pos)
                        e_type = c.get_entity_type(b_id)
                        if e_type == EntityType.BARRIER:
                            if self.is_troll or c.get_team(b_id) != my_team:
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
                else:
                    self.ores.discard(pos)

            if dist <= 10:
                bb_id = c.get_tile_builder_bot_id(pos)
                if c.get_team(bb_id) != my_team:
                    if enemy_core is not None and pos.distance_squared(enemy_core) <= 8:
                        if bb_id in targets:
                            targets.pop(bb_id)
                    else:
                        for d in C.DIRECTIONS:
                            cur = pos.add(d)
                            if U.on_the_map(cur):
                                cur_id = c.get_tile_builder_bot_id(cur)
                                if cur_id is not None and c.get_team(cur_id) == my_team and cur_id != my_id:
                                    if bb_id in targets:
                                        targets.pop(bb_id)
                                    break
                        else:
                            targets[bb_id] = pos

        self.stalker_manager.cleanse(c)
        if self.target_type <= 2:
            if self.stalker_manager.targets:
                self.target_type = 6
        elif self.target_type == 6:
            if not self.stalker_manager.targets:
                self.target_type = 0

    def run(self, c: Controller):
        super().run(c)
        my_pos = c.get_position()
        my_team = c.get_team()

        self.communication_manager.update(c)

        U.can_afford = lambda building: not c.get_action_cooldown() and c.get_global_resources()[0] >= getattr(c, f"get_{building}_cost")()[0]

        if self.target_type == 1:
            enemy_core: Position | None = self.tile_manager.enemy_core
            if enemy_core is not None and self.target.distance_squared(enemy_core) <= 2:
                if my_pos.distance_squared(enemy_core) <= 8:
                    self.target_type = 0
                    self.must_see_enemy_core = False
            else:
                if my_pos.distance_squared(self.target) <= 4 or c.get_current_round() > self.expiry:
                    self.target_type = 0

        self.tile_manager.sense(c, self.home, self.wander)
        print(c.get_cpu_time_elapsed())

        self.sense(c)
        self.movement.upd(c)
        print(c.get_cpu_time_elapsed())
        if self.target_type == 1:
            if ~(self.tile_manager.pass_bitset[self.target.y] | self.tile_manager.buildable_bitset[self.target.y]) >> self.target.x & 1:
                self.target_type = 0

        W: int = C.W
        W_plus_1: int = W + 1
        adj: list[list[int]] = self.tile_manager.network.adj

        def try_destroy():
            rem: list[Position] = [pos for pos in self.tile_manager.to_destroy if c.can_destroy(pos)]
            for pos in rem:
                c.destroy(pos)
                self.tile_manager.to_destroy.remove(pos)

        try_destroy()

        if self.tile_manager.to_destroy:
            self.nav.multimove(c, sum(1 << (y * W_plus_1 + x) for x, y in self.tile_manager.to_destroy), self.movement, adj=True)
            my_pos = c.get_position()

        try_destroy()

        to_heal: set[Position] = self.tile_manager.to_heal
        if self.target_type >= 0 and to_heal:
            def heal():
                best: Position | None = None
                max_diff: int = 4
                for pos in to_heal:
                    if c.can_heal(pos):
                        building_id = c.get_tile_building_id(pos)
                        diff: int = c.get_max_hp(building_id) - c.get_hp(building_id)
                        if diff >= max_diff:
                            best = pos
                            max_diff = diff
                if best is not None:
                    c.heal(best)
                    self.movement.act(c)
                    if max_diff == 4:
                        to_heal.remove(best)

            heal()

            if to_heal:
                self.nav.multimove(c, list(to_heal), self.movement, adj=True, active=True)
                my_pos = c.get_position()

                heal()

                if to_heal:
                    self.target_type = ~self.target_type

        lack_protection: dict[Position, Position] = {
            pos: target for pos, target in self.tile_manager.lack_protection.items() if not adj[pos.y * W + pos.x]
        }
        if 0 <= self.target_type and lack_protection:
            def build_barrier():
                if U.can_afford("conveyor"):
                    for pos, target in lack_protection.items():
                        if pos.distance_squared(my_pos) <= 2:
                            if pos == my_pos:
                                building_id = c.get_tile_building_id(pos)
                                if c.get_team(building_id) != my_team:
                                    if c.can_fire(pos):
                                        c.fire(pos)
                                        self.movement.act(c)

                            if c.can_destroy(pos):
                                c.destroy(pos)
                            d: Direction = pos.direction_to(target)
                            if c.can_build_conveyor(pos, d):
                                c.build_conveyor(pos, d)
                                lack_protection.pop(pos)
                                self.movement.act(c)
                                break

            build_barrier()

            if lack_protection:
                self.movement.enrich(c)
                self.nav.multimove(c, list(lack_protection.keys()), self.movement)
                my_pos = c.get_position()
                build_barrier()
                self.target_type = ~self.target_type

        unharvested: int = sum(1 << (y * W_plus_1 + x) for x, y in self.tile_manager.unharvested) & ~self.tile_manager["unit"]
        if 0 <= self.target_type <= 2 and unharvested:
            stay: bool = False
            if my_pos in self.tile_manager.unharvested:
                building_id = c.get_tile_building_id(my_pos)
                if c.get_team(building_id) != my_team:
                    if c.can_fire(my_pos):
                        c.fire(my_pos)
                        stay = True

            if U.can_afford("harvester"):
                self.nav.multimove(c, unharvested, self.movement, adj=True, exc=not stay)

                my_pos = c.get_position()
                for pos in self.tile_manager.unharvested:
                    if 1 <= pos.distance_squared(my_pos) <= 2:
                        if c.can_destroy(pos):
                            c.destroy(pos)
                        if c.can_build_harvester(pos):
                            c.build_harvester(pos)
                            break

                        building_id = c.get_tile_building_id(pos)
                        if c.get_team(building_id) != my_team:
                            if c.can_move(d := my_pos.direction_to(pos)):
                                self.movement.move(d)
                                my_pos = c.get_position()
                            if c.can_fire(pos):
                                c.fire(pos)
            else:
                self.nav.multimove(c, unharvested, self.movement)
                my_pos = c.get_position()

            self.target_type = ~self.target_type

        if self.target_type >= 0:
            allowed: int = C.MAP_MASK
            for mask in self.tile_manager.recently_built[-10:]:
                allowed &= ~mask
            for mask in self.tile_manager.me_built[-10:]:
                allowed |= mask

            edge: tuple = ()
            has_gunner: int = sum(1 << (y * W_plus_1 + x) for x, y in self.tile_manager.gunners)
            orphans: int = sum(1 << (index + index // W) for index in self.tile_manager.network.orphans) & allowed
            if orphans:
                print("try orphans")
                edge: tuple = ConveyorManager.get_edge(self.tile_manager, orphans & ~has_gunner)

            if not edge:
                adj_empty: int = sum(1 << (y * W_plus_1 + x) for x, y in self.tile_manager.empty_ore)
                adj_empty |= adj_empty << 1 | adj_empty >> 1 | adj_empty << W_plus_1 | adj_empty >> W_plus_1
                adj_empty &= self.tile_manager["empty"] & allowed & ~self.tile_manager.enemy

                if adj_empty:
                    print("try empty ore")
                    edge: tuple = ConveyorManager.get_edge(self.tile_manager, adj_empty & ~has_gunner)

            if edge:
                pos, nxt = edge
                if my_pos.distance_squared(pos) <= 8:
                    if pos.distance_squared(nxt) <= 2 and c.get_team(building_id := c.get_tile_building_id(nxt)) != my_team and c.get_entity_type(building_id) not in C.UNIMPORTANT:
                        self.nav.move(c, pos, self.movement, adj=True, exc=True)
                        my_pos = c.get_position()

                        if U.can_afford("gunner"):
                            if c.can_destroy(pos):
                                c.destroy(pos)
                            d: Direction = pos.direction_to(nxt)
                            if c.can_build_gunner(pos, d):
                                c.build_gunner(pos, d)
                    else:
                        if pos.distance_squared(nxt) == 1:
                            def try_build():
                                if U.can_afford("conveyor"):
                                    if c.can_destroy(pos):
                                        c.destroy(pos)
                                    d: Direction = pos.direction_to(nxt)
                                    if c.can_build_conveyor(pos, d):
                                        c.build_conveyor(pos, d)
                                        self.movement.act(c)
                                        self.tile_manager.allow(nxt)
                        else:
                            def try_build():
                                if U.can_afford("bridge"):
                                    if c.can_destroy(pos):
                                        c.destroy(pos)
                                    if c.can_build_bridge(pos, nxt):
                                        c.build_bridge(pos, nxt)
                                        self.movement.act(c)
                                        self.tile_manager.allow(nxt)

                        try_build()

                        self.nav.move(c, pos, self.movement)
                        my_pos = c.get_position()

                        if c.is_in_vision(pos):
                            building_id = c.get_tile_building_id(pos)
                            if c.get_team(building_id) != my_team and c.get_entity_type(building_id) != EntityType.MARKER:
                                if c.can_fire(pos):
                                    c.fire(pos)
                                    self.movement.act(c)


                        try_build()
                else:
                    self.nav.move(c, pos, self.movement)
                    my_pos = c.get_position()

                self.target_type = ~self.target_type
            elif orphans:
                self.nav.multimove(c, orphans, self.movement, adj=True, active=True)

        if self.target_type != 9 and self.target_type != 3:
            self.offence_manager = OffenceManager(c)
            if self.offence_manager.candidate:
                self.target_type = 3

        if self.target_type == 3:
            if not self.offence_manager.update(c, self.nav, self.movement):
                self.target_type = 0

        ever_seen: int = self.tile_manager.conveyor | self.tile_manager.bridge
        if self.target_type == 0:
            if self.must_patrol:
                if self.wander.seen == ever_seen:
                    self.must_patrol = False

            if not self.must_patrol:
                self.target = self.exploration_manager.get_target(c, self.tile_manager)
                if self.target is not None:
                    self.target_type = 1
                    self.expiry = c.get_current_round() + 260

        print(c.get_cpu_time_elapsed())
        print(self.target_type, self.target)
        if self.target_type < 0:
            self.target_type = ~self.target_type
        elif self.target_type == 0:
            self.wander.update(c, ever_seen)
        elif self.target_type == 1:
            c.draw_indicator_line(my_pos, self.target, 255, 0, 0)
            if not self.nav.multimove(c, C.MAP_MASK & ~self.tile_manager.seen, self.movement, prefer=my_pos.direction_to(self.target)):
                self.target_type = 0
                self.wander.update(c, ever_seen)
        elif self.target_type == 6:
            self.stalker_manager.update(c, self.nav, self.movement)
        elif self.target_type == 9:
            self.movement.enrich(c)
            if c.is_in_vision(self.target):
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

        if self.target_type != 4 and not c.get_action_cooldown():
            directions = list(C.DIRECTIONS)
            random.shuffle(directions)
            candidate: Position | None = None
            for d in directions:
                pos: Position = my_pos.add(d)
                if U.on_the_map(pos):
                    bb_id: int = c.get_tile_builder_bot_id(pos)
                    if bb_id is None:
                        building_id = c.get_tile_building_id(pos)
                        if building_id is not None and c.get_team(building_id) == my_team:
                            if c.get_hp(building_id) < c.get_max_hp(building_id) and c.can_heal(pos):
                                candidate = pos
                    elif c.get_hp(bb_id) < c.get_max_hp(bb_id) and c.can_heal(pos):
                        building_id = c.get_tile_building_id(pos)
                        if c.get_team(building_id) == my_team:
                            c.heal(pos)
                            self.movement.act(c)
                            break
            else:
                if candidate is not None:
                    c.heal(candidate)
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
                                self.nav.move(c, my_pos, self.movement, adj=True, exc=True, active=True)
                                break

        self.communication_manager.mark(self.tile_manager.symmetry | self.target_type << 3)

        self.tile_manager.post_sense(c)
        self.prev_resources = c.get_global_resources()[0]
