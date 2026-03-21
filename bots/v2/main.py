import random
from cambc import *
from Unit import Unit
from Core import Core
from BuilderBot import BuilderBot
from Gunner import Gunner
from Sentinel import Sentinel


class Player:
    CLASS = {
        EntityType.BUILDER_BOT: BuilderBot,
        EntityType.GUNNER: Gunner,
        EntityType.SENTINEL: Sentinel,
        EntityType.CORE: Core
    }
    def __init__(self):
        self.unit: Unit | None = None

    def run(self, c: Controller) -> None:
        if self.unit is None:
            random.seed(c.get_id())
            my_type = c.get_entity_type(c.get_id())
            self.unit = Player.CLASS[my_type]()

        try:
            self.unit.run(c)
        except Exception as e:
            raise Exception("{} {}".format(c.get_position(c.get_id()), c.get_current_round()))
