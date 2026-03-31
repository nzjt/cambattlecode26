import traceback
import sys
import random
from cambc import *
from Unit import Unit
from Core import Core
from BuilderBot import BuilderBot
from Gunner import Gunner
from Sentinel import Sentinel
from Launcher import Launcher


class Player:
    CLASS = {
        EntityType.BUILDER_BOT: BuilderBot,
        EntityType.GUNNER: Gunner,
        EntityType.SENTINEL: Sentinel,
        EntityType.LAUNCHER: Launcher,
        EntityType.CORE: Core
    }
    def __init__(self):
        self.unit: Unit | None = None
        self.safe_exit: bool = True
        self.death_msg: str = "TLE!"

    def run(self, c: Controller) -> None:
        if self.unit is None:
            random.seed(c.get_id())
            my_type = c.get_entity_type(c.get_id())
            self.unit = Player.CLASS[my_type](c)

        try:
            self.unit.run(c)
            self.safe_exit = True
        except Exception:
            self.unit = None
