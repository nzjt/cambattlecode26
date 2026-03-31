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
        if self.safe_exit:
            self.safe_exit = False

            if self.unit is None:
                random.seed(c.get_id())
                my_type = c.get_entity_type(c.get_id())
                self.unit = Player.CLASS[my_type](c)

            try:
                self.unit.run(c)
                self.safe_exit = True
            except Exception:
                self.death_msg = traceback.format_exc()
                # print(self.death_msg)
                # self.safe_exit = True
                # self.unit = None
        else:
            print(
                f"\033[0;31m{self.death_msg}\n"
                f"\033[1;33mCaused by bot {c.get_id()} at {c.get_position()}, round {c.get_current_round() - 1}\033[0m",
                file=sys.stderr
            )
            c.resign()
