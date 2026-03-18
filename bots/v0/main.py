from cambc import *
from Unit import Unit
from Core import Core
from BuilderBot import BuilderBot


class Player:
    def __init__(self):
        self.unit: Unit | None = None

    def run(self, c: Controller) -> None:
        if self.unit is None:
            my_type = c.get_entity_type(c.get_id())
            if my_type == EntityType.CORE:
                self.unit = Core()
            elif my_type == EntityType.BUILDER_BOT:
                self.unit = BuilderBot()

        self.unit.run(c)
