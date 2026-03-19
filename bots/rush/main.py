import random
from cambc import *
from Unit import Unit
from Core import Core
from BuilderBot import BuilderBot
from Gunner import Gunner


class Player:
    def __init__(self):
        self.unit: Unit | None = None

    def run(self, c: Controller) -> None:
        if self.unit is None:
            random.seed(c.get_id())
            my_type = c.get_entity_type(c.get_id())
            if my_type == EntityType.BUILDER_BOT:
                self.unit = BuilderBot()
            elif my_type == EntityType.GUNNER:
                self.unit = Gunner()
            elif my_type == EntityType.CORE:
                self.unit = Core()

        try:
            self.unit.run(c)
        except Exception as e:
            raise Exception("{} {}".format(c.get_position(c.get_id()), c.get_current_round()))
