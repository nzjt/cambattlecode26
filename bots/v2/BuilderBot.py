import random
from cambc import *
from Unit import Unit
from Movement import Movement
from Nav import Nav
from Bug0Better import Bug0Better
from ConveyorManager import ConveyorManager
from TileManager import TileManager
from Bfs import Bfs
from AStar import AStar


class BuilderBot(Unit):
    def __init__(self):
        self.movement: Movement | None = None
        self.tile_manager: TileManager | None = None
        self.nav: Nav = Bug0Better()
        self.home: Position | None = None
        self.target: Position | None = None
        self.target_type: int = 0  # 0: nothing, 1: explore, 2: go to ore, 3: build conveyor home
        self.target_dist: int = 0
        self.conveyor_manager: ConveyorManager | None = None
        self.expiry: int = 0
        self.bfs: Bfs | None = None

    def sense(self, c: Controller):
        my_id = c.get_id()
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)

        if self.target_type == 3:
            pos = self.home.add(self.home.direction_to(self.conveyor_manager.path[-1]))
            dist = self.conveyor_manager.path[-1].distance_squared(pos)
            if dist < self.target_dist:
                self.target = pos
                self.target_dist = dist
                self.conveyor_manager.update(pos)

            for pos in c.get_nearby_tiles():
                building_id = c.get_tile_building_id(pos)
                if building_id is None:
                    continue

                if c.get_entity_type(building_id) == EntityType.CONVEYOR and c.get_team(building_id) == my_team:
                    xi, yi = pos
                    if not self.conveyor_manager.on_path[yi][xi]:
                        dist = self.conveyor_manager.path[-1].distance_squared(pos)
                        if dist < self.target_dist:
                            if self.bfs.can_conveyor_reach(xi - my_pos.x, yi - my_pos.y):
                                good = True
                                cur = pos
                                for _ in range(10):
                                    building_id = c.get_tile_building_id(cur)
                                    if building_id is None or c.get_team(building_id) != my_team:
                                        good = False
                                        break
                                    e_type = c.get_entity_type(building_id)
                                    if e_type != EntityType.CONVEYOR:
                                        good = e_type == EntityType.CORE
                                        break
                                    cur = cur.add(c.get_direction(building_id))
                                    if c.is_in_vision(cur):
                                        if self.conveyor_manager.on_path[cur.y][cur.x]:
                                            good = False
                                            break
                                    else:
                                        # Probably fine?
                                        break

                                if good:
                                    self.target = pos
                                    self.target_dist = dist
                                    self.conveyor_manager.update(pos)
        else:
            for pos in c.get_nearby_tiles():
                env: Environment = c.get_tile_env(pos)
                if env == Environment.ORE_TITANIUM or env == Environment.ORE_AXIONITE:
                    if not self.tile_manager.build_harvester[pos.y][pos.x]:
                        continue

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
        my_pos = c.get_position(my_id)
        my_team = c.get_team(my_id)

        if self.home is None:
            self.home = c.get_position(c.get_tile_building_id(my_pos))
            self.movement = Movement()
            self.tile_manager = TileManager(c)
            self.bfs = Bfs(self.tile_manager)
            AStar.precomp(c.get_map_width(), c.get_map_height(), *self.home)

        if self.target_type == 1:
            if my_pos.distance_squared(self.target) <= 4 or c.get_current_round() > self.expiry:
                self.target_type = 0
        elif self.target_type == 2:
            if c.is_in_vision(self.target):
                bb_id = c.get_tile_builder_bot_id(self.target)
                if bb_id is not None and bb_id != my_id:
                    self.target_type = 0
        elif self.target_type == 3:
            if c.is_in_vision(self.conveyor_manager.path[-1]):
                dist = my_pos.distance_squared(self.target)
                self.target_dist = min(self.target_dist, dist)

                if self.target == self.home:
                    if dist <= 5:
                        self.target_type = 0
                else:
                    if dist <= 1:
                        self.target_type = 0
            else:
                self.target_type = 0

        self.tile_manager.sense(c)
        self.bfs.update(c, self.conveyor_manager)

        if self.target_type == 2:
            if not self.tile_manager.build_harvester[self.target.y][self.target.x]:
                self.target_type = 0

            if self.target_type:
                dist = my_pos.distance_squared(self.target)
                self.target_dist = min(self.target_dist, dist)

                if dist == 0:
                    self.target = self.home.add(self.home.direction_to(my_pos))
                    self.target_type = 3
                    self.target_dist = my_pos.distance_squared(self.target)
                    self.conveyor_manager = ConveyorManager(c, my_pos, self.target)
                elif dist == 1:
                    building_id = c.get_tile_building_id(self.target)
                    if c.get_entity_type(building_id) == EntityType.HARVESTER:
                        harvester: Position = self.target
                        self.target = self.home.add(self.home.direction_to(my_pos))
                        self.target_type = 3
                        self.target_dist = my_pos.distance_squared(self.target)
                        self.conveyor_manager = ConveyorManager(c, harvester, self.target)

                if self.target_type == 3:
                    self.conveyor_manager.step(c)
                    if len(self.conveyor_manager.path) == 1:
                        xi, yi = self.conveyor_manager.path[0]
                        self.tile_manager.ban_harvester[yi][xi] = True
                        self.target_type = 0
                    else:
                        a_star = AStar(self.tile_manager, c.get_map_width(), c.get_map_height())
                        a_star.compute(self.conveyor_manager.path[0], self.target)
                        a_star.find_path(self.home)
                        path = a_star.path
                        for i in range(1, len(path)):
                            c.draw_indicator_line(path[i - 1], path[i], 255, 0, 255)

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
            if my_pos == self.conveyor_manager.path[0] and self.target.distance_squared(self.conveyor_manager.path[0]) == 1:
                if not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_harvester_cost()[0]:
                    for d in Direction:
                        if c.can_move(d):
                            nxt = my_pos.add(d)
                            if 1 <= nxt.distance_squared(self.conveyor_manager.path[0]) <= 2:
                                self.movement.move(d)

                                if c.can_destroy(self.conveyor_manager.path[0]):
                                    c.destroy(self.conveyor_manager.path[0])

                                c.build_harvester(self.conveyor_manager.path[0])
                                self.target_type = 0
                                break
            else:
                building_id = c.get_tile_building_id(self.conveyor_manager.path[-1])
                if c.get_entity_type(building_id) == EntityType.CONVEYOR and c.get_team(building_id) == my_team:
                    self.conveyor_manager.step(c)

                conveyor_target: Position = self.conveyor_manager.path[-1]
                building_id = c.get_tile_building_id(conveyor_target)
                if building_id is not None and c.get_entity_type(building_id) == EntityType.ROAD:
                    if c.can_destroy(conveyor_target):
                        c.destroy(conveyor_target)

                if c.can_build_conveyor(conveyor_target, Direction.NORTH):
                    self.conveyor_manager.step(c)
                    if not self.conveyor_manager.place(c, conveyor_target):
                        print("wtf")
                        self.target_type = 0
                        xi, yi = self.conveyor_manager.path[0]
                        self.tile_manager.ban_harvester[yi][xi] = True

                do_build = (my_pos == self.conveyor_manager.path[0] and
                            len(self.conveyor_manager.path) > 1 and
                            c.get_team(c.get_tile_building_id(self.conveyor_manager.path[0])) == my_team)

                if my_pos.distance_squared(self.conveyor_manager.path[-1]) > 1:
                    if not do_build or not c.get_action_cooldown() and c.get_global_resources()[0] >= c.get_harvester_cost()[0]:
                        if do_build:
                            d = my_pos.direction_to(self.conveyor_manager.path[1])
                        else:
                            building_id = c.get_tile_building_id(my_pos)
                            if c.get_entity_type(building_id) == EntityType.CONVEYOR:
                                d = c.get_direction(building_id)
                            else:
                                xi, yi = self.conveyor_manager.path[-1]
                                pass_ = self.tile_manager.pass_ & ~self.tile_manager.ally & ~self.tile_manager.enemy
                                d = self.bfs.bfs_adj_exc(xi - my_pos.x, yi - my_pos.y, pass_)

                        if d is not None and c.can_move(d):
                            self.movement.move_raw(d)

                            if do_build:
                                if c.can_destroy(my_pos):
                                    c.destroy(my_pos)

                                c.build_harvester(my_pos)

                c.draw_indicator_line(my_pos, self.target, 0, 0, 255)
                c.draw_indicator_line(my_pos, self.conveyor_manager.path[-1], 0, 255, 255)
