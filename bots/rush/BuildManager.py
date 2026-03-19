from cambc import *


class BuildManager:
    def __init__(self):
        self.c: Controller | None = None

    def update(self, c: Controller):
        self.c = c

    def can_build(self, pos: Position) -> bool:
        if self.c.get_tile_env(pos) == Environment.WALL:
            return False
        building_id = self.c.get_tile_building_id(pos)
        if building_id is None:
            return True
        if self.c.get_team(building_id) != self.c.get_team(self.c.get_id()):
            return False
        e_type = self.c.get_entity_type(building_id)
        if e_type == EntityType.ROAD or e_type == EntityType.CONVEYOR:
            return True
