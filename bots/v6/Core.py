from random import random

from cambc import *
from Unit import Unit
from SpawnManager import SpawnManager
import consts as C
import random


class Core(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)
        self.tracker: dict[Position, int] = {}
        self.has_tried_foundry: bool = False
        self.spawn_manager = SpawnManager()

        my_pos = c.get_position()
        directions: list[Direction] = list(C.DIRECTIONS)
        random.shuffle(directions)
        self.spawn_manager.queue = [my_pos.add(d) for d in directions[:3]]

    def run(self, c: Controller):
        super().run(c)
        my_pos = c.get_position(c.get_id())

        if c.get_current_round() <= 1900:
            ti, ax = c.get_global_resources()
            needed_titanium: int = c.get_builder_bot_cost()[0] - ti
            if needed_titanium > 0:
                if ax * 4 <= needed_titanium:
                    c.convert(ax)
                else:
                    c.convert((needed_titanium + 3) // 4)

        for building_id in c.get_nearby_buildings(5):
            if c.get_entity_type(building_id) == EntityType.CONVEYOR:
                pos: Position = c.get_position(building_id)
                if pos.add(c.get_direction(building_id)).distance_squared(my_pos) <= 2:
                    resource: ResourceType = c.get_stored_resource(building_id)
                    val: int = self.tracker.get(pos, 0)
                    if resource == ResourceType.TITANIUM:
                        val |= 1
                    elif resource == ResourceType.RAW_AXIONITE:
                        val |= 2

                    self.tracker[pos] = val

        if c.get_current_round() <= 2:
            self.spawn_manager.spawn(c)
        # elif c.get_current_round() >= 150 and any(v == 3 for v in self.tracker.values()) and not self.has_tried_foundry:
        #     for d in Direction:
        #         pos = my_pos.add(d)
        #         if c.can_spawn(pos):
        #             self.has_tried_foundry = True
        #             c.spawn_builder(pos)
        #             break
        elif self.tracker or c.get_current_round() >= 150:
            if c.get_global_resources()[0] >= 300 and c.get_global_resources()[0] * 2.5 >= c.get_scale_percent():
                self.spawn_manager.spawn(c)
            elif self.tracker and self.spawn_manager.spawned < 6:
                self.spawn_manager.spawn(c)
