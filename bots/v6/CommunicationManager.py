from cambc import *
import consts as C
import random


class CommunicationManager:
    def __init__(self):
        self.c: Controller | None = None

    def update(self, c: Controller):
        self.c = c

    def mark(self, message: int):
        c: Controller = self.c
        my_pos = self.c.get_position()
        my_team = c.get_team()

        directions: list[Position] = list(C.DIRECTIONS)
        random.shuffle(directions)
        for d in directions:
            pos: Position = my_pos.add(d)
            if c.can_place_marker(pos):
                building_id = c.get_tile_building_id(pos)
                if c.get_entity_type(building_id) == EntityType.MARKER and c.get_team(building_id) == my_team:
                    continue
                c.place_marker(pos, message)
                return