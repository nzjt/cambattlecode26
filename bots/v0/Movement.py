from cambc import *


class Movement:
    def __init__(self, c: Controller):
        self.c = c

    def can_move(self, d: Direction) -> bool:
        c: Controller = self.c
        if c.can_move(d):
            return True

        if c.get_action_cooldown():
            return False
        else:
            nxt: Position = c.get_position(c.get_id()).add(d)
            return c.can_build_road(nxt) and c.get_tile_builder_bot_id(nxt) is None

    def move(self, d: Direction):
        c: Controller = self.c
        if c.can_move(d):
            c.move(d)
            return

        c.build_road(c.get_position(c.get_id()).add(d))
        c.move(d)