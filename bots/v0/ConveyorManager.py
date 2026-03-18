import random
from cambc import *


class ConveyorManager:
    def __init__(self, c: Controller, target: Position):
        W: int = c.get_map_width()
        self.on_path = [[False] * W for _ in range(c.get_map_height())]
        self.path: list[Position] = [c.get_position(c.get_id())]
        self.target: Position = target
        self.turn: bool | None = None
        self.dist: int = 0

    def step(self, c: Controller):
        cur: Position = self.path[-1]

        if cur == self.target or cur.distance_squared(c.get_position(c.get_id())) > 13:
            return

        dx = cur.x - self.target.x
        dy = cur.y - self.target.y
        if random.randint(1, abs(dx) + abs(dy)) <= abs(dx):
            opt: Direction = Direction.WEST if dx > 0 else Direction.EAST
        else:
            opt: Direction = Direction.NORTH if dy > 0 else Direction.SOUTH
        team = c.get_team(c.get_id())
        W = c.get_map_width()
        H = c.get_map_height()

        def can_move(nxt: Position):
            if nxt == self.target:
                return True
            if 0 <= nxt.x <= W - 1 and 0 <= nxt.y <= H - 1:
                if c.get_tile_env(nxt) != Environment.EMPTY:
                    return False
                building_id = c.get_tile_building_id(nxt)
                if building_id is None:
                    return True
                if c.get_team(building_id) != team:
                    return False
                e_type = c.get_entity_type(building_id)
                return e_type == EntityType.ROAD or e_type == EntityType.CORE
            else:
                return False

        if len(self.path) >= 2 and self.turn is not None:
            d = self.path[-2].direction_to(self.path[-1])
            if self.turn:
                d = d.rotate_right().rotate_right()
            else:
                d = d.rotate_left().rotate_left()
        else:
            d = opt

        dist = self.path[-1].distance_squared(self.target)
        nxt = cur.add(opt)
        if can_move(nxt):
            if self.turn is None:
                self.path.append(nxt)
                return
            elif dist < self.dist:
                self.turn = None
                self.path.append(nxt)
                return
        elif self.turn is None:
            self.turn = bool(random.randint(0, 1))
            self.dist = self.path[-1].distance_squared(self.target)

        counter = 2
        while counter > 0:
            counter -= 1
            if self.turn:
                # Left turning
                for _ in range(3):
                    nxt = cur.add(d)

                    if self.on_path[nxt.y][nxt.x]:
                        self.turn = False
                        d = opt
                        break
                    elif can_move(nxt):
                        counter = -1
                        break

                    d = d.rotate_left().rotate_left()
                else:
                    return
            else:
                # Right turning
                for _ in range(3):
                    nxt = cur.add(d)

                    if self.on_path[nxt.y][nxt.x]:
                        self.turn = True
                        d = opt
                        break
                    elif can_move(nxt):
                        counter = -1
                        break

                    d = d.rotate_right().rotate_right()
                else:
                    return

        if not counter:
            return

        self.path.append(cur.add(d))

    def place(self, c: Controller, pos: Position) -> bool:
        if self.path[-1].distance_squared(pos) != 1:
            return False

        c.build_conveyor(pos, pos.direction_to(self.path[-1]))
        self.on_path[pos.y][pos.x] = True
        return True

    def update(self, target: Position):
        if target != self.target:
            self.target = target
            if self.turn is not None:
                self.dist = self.path[-1].distance_squared(target)
