import pygame

from dark_libraries.dark_math import Vector2

DIRECTION_MAP = {
    pygame.K_LEFT  : Vector2[int](-1, 0),
    pygame.K_RIGHT : Vector2[int](+1, 0),
    pygame.K_UP    : Vector2[int](0, -1),
    pygame.K_DOWN  : Vector2[int](0, +1)
}

DIRECTION_NAMES = {
    Vector2[int](-1, 0) : "West",
    Vector2[int](+1, 0) : "East",
    Vector2[int](0, -1) : "North",
    Vector2[int](0, +1) : "South"
}
