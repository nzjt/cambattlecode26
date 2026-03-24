from cambc import *


class Movement:
    def __init__(self):
        self.c: Controller | None = None
        self.can_move = None
        self.move_ = None

    def upd(self, c: Controller):
        self.c = c
        delta = c.get_global_resources()[0] - c.get_foundry_cost()[0]
        if delta >= c.get_road_cost()[0]:
            self.can_move = self.can_move_rich
            self.move_ = self.move_rich
        else:
            self.can_move = c.can_move
            self.move_ = c.move

    def can_move_rich(self, d: Direction) -> bool:
        c: Controller = self.c
        if c.can_move(d):
            return True

        if c.get_action_cooldown():
            return False
        else:
            nxt: Position = c.get_position(c.get_id()).add(d)
            return c.can_build_road(nxt) and c.get_tile_builder_bot_id(nxt) is None

    def move_raw(self, d: Direction):
        self.c.move(d)

    def move_rich(self, d: Direction):
        c: Controller = self.c
        if c.can_move(d):
            self.move_raw(d)
            return

        c.build_road(c.get_position(c.get_id()).add(d))
        self.move_raw(d)
