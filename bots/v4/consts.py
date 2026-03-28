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
    EntityType.MARKER,
    EntityType.ROAD,
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.SPLITTER
}
