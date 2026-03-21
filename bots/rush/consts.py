from cambc import *


CARDINAL = (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)
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
