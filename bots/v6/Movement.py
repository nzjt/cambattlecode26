from cambc import *
import consts as C


class Movement:
    def __init__(self):
        self.c: Controller | None = None
        self.can_move = None
        self.move = None
        self.is_rich: bool = False

    def upd(self, c: Controller, emergency: bool = False):
        self.c = c
        delta = c.get_global_resources()[0] - c.get_foundry_cost()[0]
        if delta >= c.get_road_cost()[0] and not c.get_action_cooldown():
            if emergency:
                self.can_move = self.can_move_rich_emergency
                self.move = self.move_rich_emergency
            else:
                self.can_move = self.can_move_rich
                self.move = self.move_rich
            self.is_rich = True
        else:
            self.can_move = c.can_move
            self.move = c.move
            self.is_rich = False

    def act(self, c: Controller):
        self.can_move = c.can_move
        self.move = c.move
        self.is_rich = False

    def enrich(self, c: Controller):
        if c.get_global_resources()[0] >= c.get_road_cost()[0]:
            self.can_move = self.can_move_rich
            self.move = self.move_rich
            self.is_rich = True

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

        c.build_road(c.get_position().add(d))
        self.move_raw(d)

    def can_move_rich_emergency(self, d: Direction) -> bool:
        c: Controller = self.c
        if c.can_move(d):
            return True

        if c.get_action_cooldown():
            return False
        else:
            nxt: Position = c.get_position().add(d)
            if c.get_tile_builder_bot_id(nxt) is None:
                building_id = c.get_tile_building_id(nxt)
                if building_id is None:
                    return c.can_build_road(nxt)
                else:
                    return c.get_team(building_id) == c.get_team() and c.get_entity_type(building_id) in C.EMERGENCY_DESTROY
            else:
                return False

    def move_rich_emergency(self, d: Direction):
        c: Controller = self.c
        if c.can_move(d):
            self.move_raw(d)
            return

        nxt: Position = c.get_position().add(d)
        if c.can_destroy(nxt):
            c.destroy(nxt)
        c.build_road(nxt)
        self.move_raw(d)
