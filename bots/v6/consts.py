from cambc import *


CARDINAL = (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)
UNIMPORTANT = {
    EntityType.ROAD,
    EntityType.MARKER
}
CONVEYOR = {
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR
}
CONVEYOR_VARIANT = {
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.SPLITTER
}
MONOCHILD_CONVEYOR = {
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE
}
TURRET = {
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH
}
DIRECTIONS = (
    Direction.NORTH,
    Direction.NORTHEAST,
    Direction.EAST,
    Direction.SOUTHEAST,
    Direction.SOUTH,
    Direction.SOUTHWEST,
    Direction.WEST,
    Direction.NORTHWEST
)
EMERGENCY_DESTROY = {
    EntityType.MARKER,
    EntityType.ROAD,
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.SPLITTER,
    EntityType.BARRIER
}
DESTROY_ENEMY = {
    EntityType.ROAD,
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.SPLITTER
}
ORDINAL = {
    Direction.NORTH: 0,
    Direction.NORTHEAST: 1,
    Direction.EAST: 2,
    Direction.SOUTHEAST: 3,
    Direction.SOUTH: 4,
    Direction.SOUTHWEST: 5,
    Direction.WEST: 6,
    Direction.NORTHWEST: 7
}
CAN_BUILD_LAUNCHER = {
    None,
    EntityType.MARKER,
    EntityType.ROAD,
    EntityType.BARRIER
}
CHAMBER_WALL = {
    EntityType.ROAD,
    EntityType.CORE,
    EntityType.BARRIER,
    EntityType.LAUNCHER
}
DANGEROUS = {
    EntityType.CORE,
    EntityType.BARRIER
} | TURRET
DIRECTION_MAP = {
    (0, -1): Direction.NORTH,
    (1, -1): Direction.NORTHEAST,
    (1, 0): Direction.EAST,
    (1, 1): Direction.SOUTHEAST,
    (0, 1): Direction.SOUTH,
    (-1, 1): Direction.SOUTHWEST,
    (-1, 0): Direction.WEST,
    (-1, -1): Direction.NORTHWEST,
}
W: int = 0
H: int = 0
