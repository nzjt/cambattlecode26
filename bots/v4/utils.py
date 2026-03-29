from cambc import *


def normalise_on_grid(waypoints: list[Position], env_grid: list[list[int]]):
    path: list[Position] = [waypoints[0]]
    parity: bool = False
    bridge: bool = False
    for way_point in waypoints:
        d: Direction = path[-1].direction_to(way_point)
        while path[-1] != way_point:
            # if bridge:
            #     if path[-1].add(d).distance_squared(path[-2]) <= 9:
            #         path[-1] = path[-1].add(d)
            #         continue
            #     else:
            #         bridge = False

            dx, dy = d.delta()
            if dx and dy:
                x, y = path[-1]
                if path[-1].add(d) != way_point:
                    if env_grid[y][x + dx] == 2 and env_grid[y][x + dx * 2] == 2 and env_grid[y + dy][x + dx * 2] == 2:
                        path.append(Position(x + dx, y))
                        path.append(Position(x + dx * 2, y))
                        path.append(Position(x + dx * 2, y + dy))
                        path.append(Position(x + dx * 2, y + dy * 2))
                        parity = False
                        continue
                    elif env_grid[y + dy][x] == 2 and env_grid[y + dy * 2][x] == 2 and env_grid[y + dy * 2][x + dx] == 2:
                        path.append(Position(x, y + dy))
                        path.append(Position(x, y + dy * 2))
                        path.append(Position(x + dx, y + dy * 2))
                        path.append(Position(x + dx * 2, y + dy * 2))
                        parity = True
                        continue

                if parity:
                    if env_grid[y][x + dx] == 2:
                        path.append(Position(x + dx, y))
                        parity = False
                    elif env_grid[y + dy][x] == 2:
                        path.append(Position(x, y + dy))
                    else:
                        bridge = True
                else:
                    if env_grid[y + dy][x] == 2:
                        path.append(Position(x, y + dy))
                        parity = True
                    elif env_grid[y][x + dx] == 2:
                        path.append(Position(x + dx, y))
                    else:
                        bridge = True
                path.append(Position(x + dx, y + dy))
            else:
                path.append(path[-1].add(d))
                parity = bool(dx)
    return path


def normalise(waypoints: list[Position], max_len: int = -1):
    path: list[Position] = [waypoints[0]]
    for way_point in waypoints:
        d: Direction = path[-1].direction_to(way_point)
        while path[-1] != way_point:
            path.append(path[-1].add(d))
            if len(path) == max_len:
                return path

    return path
