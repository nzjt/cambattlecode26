from cambc import *
from Unit import Unit


class Core(Unit):
    def __init__(self, c: Controller):
        super().__init__(c)
        self.tracker: dict[Position, int] = {}
        self.has_tried_foundry: bool = False

    def run(self, c: Controller):
        super().run(c)
        my_pos = c.get_position(c.get_id())

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

        if c.get_current_round() <= 5:
            for d in Direction:
                pos = my_pos.add(d)
                if c.can_spawn(pos):
                    c.spawn_builder(pos)
                    break
        # elif c.get_current_round() >= 150 and any(v == 3 for v in self.tracker.values()) and not self.has_tried_foundry:
        #     for d in Direction:
        #         pos = my_pos.add(d)
        #         if c.can_spawn(pos):
        #             self.has_tried_foundry = True
        #             c.spawn_builder(pos)
        #             break
        elif c.get_current_round() >= 100:
            if c.get_global_resources()[0] >= 800:
                for d in Direction:
                    pos = my_pos.add(d)
                    if c.can_spawn(pos):
                        c.spawn_builder(pos)
                        break

