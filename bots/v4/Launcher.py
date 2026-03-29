import random
from math import frexp

from cambc import *
from Unit import *
from consts import *


class Launcher(Unit):
    def run(self, c: Controller):
        my_pos = c.get_position()
        my_team = c.get_team()
        W, H = c.get_map_width(), c.get_map_height()

        best: Position | None = None
        best_score: int = 0
        for pos in c.get_nearby_tiles():
            building_id = c.get_tile_building_id(pos)
            if c.get_entity_type(building_id) == EntityType.CORE:
                if c.get_team(building_id) == my_team:
                    continue
            elif not c.is_tile_passable(pos):
                if c.get_entity_type(building_id) == EntityType.GUNNER:
                    if c.get_team(building_id) == my_team:
                        nxt = pos.add(c.get_direction(building_id))
                        if c.is_in_vision(nxt) and c.is_tile_passable(nxt):
                            best = nxt
                            best_score = -1
                            break
                continue

            if c.get_entity_type(building_id) in CONVEYOR_VARIANT and c.get_team(building_id) == my_team:
                continue

            dist = max(abs(pos.x - my_pos.x), abs(pos.y - my_pos.y))
            score = dist << 12 | random.randint(0, 0xFFF)
            if score > best_score:
                best = pos
                best_score = score

        if best_score != -1:
            cur = None
            for d in DIRECTIONS:
                cur = my_pos.add(d)
                if 0 <= cur.x < W and 0 <= cur.y < H:
                    building_id = c.get_tile_building_id(cur)
                    if c.get_entity_type(building_id) in CONVEYOR_VARIANT:
                        break

            if cur is not None:
                friend = None
                while True:
                    building_id = c.get_tile_building_id(cur)
                    e_type = c.get_entity_type(building_id)
                    if e_type in MONOCHILD_CONVEYOR:
                        cur = cur.add(c.get_direction(building_id))
                    elif e_type == EntityType.BRIDGE:
                        cur = c.get_bridge_target(building_id)
                    else:
                        break

                    if not c.is_in_vision(cur):
                        break

                    for d in DIRECTIONS:
                        nxt = cur.add(d)
                        if 0 <= nxt.x < W and 0 <= nxt.y < H and c.is_in_vision(nxt):
                            b_id = c.get_tile_building_id(nxt)
                            if b_id is not None and c.get_entity_type(b_id) == EntityType.LAUNCHER:
                                if c.get_team(b_id) == my_team:
                                    friend = nxt

                if friend is not None and friend != my_pos:
                    c.draw_indicator_line(my_pos, friend, 0, 128, 255)
                    for d in DIRECTIONS:
                        nxt = friend.add(d)
                        if 0 <= nxt.x < W and 0 <= nxt.y < H and c.is_in_vision(nxt):
                            if c.is_tile_passable(nxt):
                                best = nxt
                                break

        if best is None:
            return

        best_enemy: Position | None = None
        for bb_id in c.get_nearby_units(2):
            if c.get_team(bb_id) == my_team:
                continue

            pos = c.get_position(bb_id)
            building_id = c.get_tile_building_id(pos)
            if c.can_launch(pos, best):
                if c.get_entity_type(building_id) in CONVEYOR_VARIANT and c.get_team(building_id) == my_team:
                    c.launch(pos, best)
                    return
                best_enemy = pos  # TODO

        if best_enemy is not None:
            c.launch(best_enemy, best)
