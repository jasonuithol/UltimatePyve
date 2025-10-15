import pygame

from dark_libraries.logging   import LoggerMixin
from data.global_registry     import GlobalRegistry
from models.enums.cursor_type import CursorType
from models.sprite import DEFAULT_FRAME_TIME, Sprite
from models.tile import Tile

BLACK = (0,0,0)
WHITE = (255,255,255)
TRANSPARENT = (1,2,3)

TILE_SIZE = 16

# cursor: outline
BORDER_THICCNESS = 3
BORDER_OFFSET = 1

# cursor: crosshair
OUTER_BORDER = 2
INNER_BORDER = 6

def _get_cursor_surface():
    surf = pygame.Surface((TILE_SIZE,TILE_SIZE))
    surf.fill(TRANSPARENT)
    surf.set_colorkey(TRANSPARENT)
    return surf

def _rotate_point_90_clockwise(point: tuple[int,int]) -> tuple[int,int]:
    x, y = point
    c = (TILE_SIZE - 1) / 2  # geometric centre
    # translate
    x_shift, y_shift = x - c, y - c
    # rotate clockwise
    x_rot, y_rot = y_shift, -x_shift
    # translate back
    return int(x_rot + c), int(y_rot + c)

BLANK_TILE = Tile(None, None, _get_cursor_surface())

def draw_cursor_outline():
    surf = _get_cursor_surface()
    rect = (
        BORDER_OFFSET,  # x
        BORDER_OFFSET,  # y
        TILE_SIZE,      # width
        TILE_SIZE       # height
    )
    pygame.draw.rect(surf, WHITE, rect, BORDER_THICCNESS)
    return surf

def draw_cursor_crosshair():
    surf = _get_cursor_surface()
    vertices = [
        (INNER_BORDER, OUTER_BORDER),
        (INNER_BORDER, INNER_BORDER),
        (OUTER_BORDER, INNER_BORDER)
    ]
    for _ in range(4):
        pygame.draw.line(surf, WHITE, vertices[0], vertices[1], 1)
        pygame.draw.line(surf, WHITE, vertices[1], vertices[2], 1)
        vertices = [_rotate_point_90_clockwise(v) for v in vertices]
    return surf

def create_sprite(surf: pygame.Surface) -> Sprite:
    on_tile = Tile(
        tile_id = None,
        pixels  = None,
        surface = surf
    )

    return Sprite(
        frames     = [on_tile, BLANK_TILE],
        frame_time = DEFAULT_FRAME_TIME / 2
    )

class CursorLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def load(self):
        self.global_registry.cursors.register(CursorType.OUTLINE.value, create_sprite(draw_cursor_outline()))
        self.global_registry.cursors.register(CursorType.CROSSHAIR.value, create_sprite(draw_cursor_crosshair()))
        self.log(f"Registered {len(self.global_registry.cursors)} cursors.")
