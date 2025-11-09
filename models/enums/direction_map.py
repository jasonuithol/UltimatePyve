from enum import Enum
import pygame

from dark_libraries.dark_math import Vector2

NORTH = Vector2[int]( 0, -1)
SOUTH = Vector2[int]( 0, +1)
EAST  = Vector2[int](+1,  0)
WEST  = Vector2[int](-1,  0)

class DirectionVector(Enum):
    NORTH = NORTH
    SOUTH = SOUTH
    EAST  = EAST
    WEST  = WEST
    
DIRECTION_MAP = {
    pygame.K_LEFT  : WEST,
    pygame.K_RIGHT : EAST,
    pygame.K_UP    : NORTH,
    pygame.K_DOWN  : SOUTH
}

DIRECTION_NAMES = {
    WEST  : "West",
    EAST  : "East",
    NORTH : "North",
    SOUTH : "South"
}

NORTH_WEST = Vector2[int](-1, -1)
NORTH_EAST = Vector2[int](+1, -1)
SOUTH_EAST = Vector2[int](+1, +1)
SOUTH_WEST = Vector2[int](-1, +1)

DIRECTION_SECTORS = {
    NORTH : (NORTH_WEST, NORTH_EAST),  # NW, NE
    SOUTH : (SOUTH_EAST, SOUTH_WEST),  # SE, SW
    EAST  : (NORTH_EAST, SOUTH_EAST),  # NE, SE
    WEST  : (SOUTH_WEST, NORTH_WEST),  # SW, NW
}


