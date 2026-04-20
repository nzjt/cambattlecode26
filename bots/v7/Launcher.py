from cambc import *
from Unit import *
import consts as C


class Launcher(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)

    def run(self, c: Controller):
        super().run(c)
        my_pos = c.get_position()
        my_team = c.get_team()

        has_input: list[list[bool]] = [[False] * C.W for _ in range(C.H)]
        adj_launcher: list[list[bool]] = [[False] * C.W for _ in range(C.H)]
        for building_id in c.get_nearby_buildings():
            e_type = c.get_entity_type(building_id)
            if e_type in C.CONVEYOR:
                nxt: Position = c.get_position(building_id).add(c.get_direction(building_id))
                if U.on_the_map(nxt):
                    x, y = nxt
                    has_input[y][x] = True
            elif e_type == EntityType.BRIDGE:
                nxt: Position = c.get_bridge_target(building_id)
                if U.on_the_map(nxt):
                    x, y = nxt
                    has_input[y][x] = True
            elif e_type == EntityType.LAUNCHER:
                if c.get_team(building_id) == my_team:
                    pos: Position = c.get_position(building_id)
                    for d in C.CARDINAL:
                        adj: Position = pos.add(d)
                        if U.on_the_map(adj):
                            x, y = adj
                            adj_launcher[y][x] = True
            elif e_type == EntityType.SPLITTER:
                pos: Position = c.get_position(building_id)
                d: Direction = c.get_direction(building_id).opposite()
                for e in C.CARDINAL:
                    if e != d:
                        nxt: Position = pos.add(e)
                        if U.on_the_map(nxt):
                            x, y = nxt
                            has_input[y][x] = True

        protect: list[Position] = []
        for pos in c.get_nearby_tiles():
            x, y = pos
            if has_input[y][x] and adj_launcher[y][x]:
                building_id = c.get_tile_building_id(pos)
                if c.get_team(building_id) == my_team:
                    if c.get_entity_type(building_id) == EntityType.ROAD:
                        protect.append(pos)
                else:
                    if c.get_hp(building_id) < c.get_max_hp(building_id):
                        protect.append(pos)
                    elif c.get_entity_type(building_id) in C.CONVEYOR_VARIANT:
                        bb_id = c.get_tile_builder_bot_id(pos)
                        if bb_id is not None and c.get_team(bb_id) == my_team:
                            protect.append(pos)

        if all(pos.distance_squared(my_pos) > 1 for pos in protect) and all(c.get_entity_type(bb_id) != EntityType.BUILDER_BOT or c.get_team(bb_id) != my_team for bb_id in c.get_nearby_units(4)):
            c.self_destruct()
            return

        if protect:
            for pos in protect:
                c.draw_indicator_line(my_pos, pos, 0, 128, 255)

                def get_dist(pos: Position) -> int:
                    return max(pos.distance_squared(cur) for cur in protect)

                best_enemy: Position | None = None
                best_dist: int = 100
                for bb_id in c.get_nearby_units():
                    if c.get_entity_type(bb_id) != EntityType.BUILDER_BOT:
                        continue
                    pos: Position = c.get_position(bb_id)
                    if pos.distance_squared(my_pos) <= 2:
                        if c.get_team(bb_id) != my_team:
                            dist: int = get_dist(pos)
                            if dist < best_dist:
                                best_enemy = pos
                                best_dist = dist

                best_throw: Position | None = None
                best_dist: int = 0
                if best_enemy is not None:
                    for pos in c.get_nearby_tiles():
                        if c.can_launch(best_enemy, pos):
                            dist: int = get_dist(pos)
                            if dist > best_dist:
                                best_throw = pos
                                best_dist = dist

                    if best_throw is not None:
                        c.launch(best_enemy, best_throw)
