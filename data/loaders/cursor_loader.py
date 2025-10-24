import pygame

from dark_libraries.logging   import LoggerMixin
from data.global_registry     import GlobalRegistry
from models.enums.cursor_type import CursorType
from models.sprite            import Sprite
from models.tile              import Tile
from services.surface_factory import SurfaceFactory
from view.display_config import DisplayConfig

BLACK = (0,0,0)
WHITE = (200,200,200)
TRANSPARENT = (1,2,3)

CURSOR_FRAME_DURATION_SECONDS = 0.25

# cursor: outline
BORDER_THICCNESS = 3
BORDER_OFFSET = 0

# cursor: crosshair
OUTER_BORDER = 2
INNER_BORDER = 6



class CursorLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry
    surface_factory: SurfaceFactory
    display_config:  DisplayConfig

    def load(self):
        self._blank_tile = Tile(None, None, self._get_cursor_surface())

        self.global_registry.cursors.register(CursorType.OUTLINE.value,   self._create_sprite(self._build_cursor_outline()))
        self.global_registry.cursors.register(CursorType.CROSSHAIR.value, self._create_sprite(self._build_cursor_crosshair()))
        self.log(f"Registered {len(self.global_registry.cursors)} cursors.")

    def _get_cursor_surface(self):
        surf = self.surface_factory.create_surface(self.display_config.TILE_SIZE)
        surf.fill(TRANSPARENT)
        surf.set_colorkey(TRANSPARENT)
        return surf
    
    def _create_sprite(self, surf: pygame.Surface) -> Sprite[Tile]:
        on_tile = Tile(
            tile_id = None,
            pixels  = None,
            surface = surf
        )

        return Sprite[Tile](
            [on_tile, self._blank_tile],
            CURSOR_FRAME_DURATION_SECONDS
        )
        
    def _build_cursor_outline(self):
        surf = self._get_cursor_surface()
        rect = (
            BORDER_OFFSET,  # x
            BORDER_OFFSET,  # y
            self.display_config.TILE_SIZE.w,      # width
            self.display_config.TILE_SIZE.h       # height
        )
        pygame.draw.rect(surf, WHITE, rect, BORDER_THICCNESS)
        return surf

    def _build_cursor_crosshair(self):
        surf = self._get_cursor_surface()

        # a backwards L
        white_vertices = [
            (INNER_BORDER, OUTER_BORDER), # middle, top
            (INNER_BORDER, INNER_BORDER), # middle, middle
            (OUTER_BORDER, INNER_BORDER)  # left  , middle
        ]

        black_vertices = [
            (INNER_BORDER + 1, OUTER_BORDER), # middle, top
            (INNER_BORDER + 1, INNER_BORDER), # middle, middle

            (INNER_BORDER, INNER_BORDER + 1), # middle, middle
            (OUTER_BORDER, INNER_BORDER + 1)  # left  , middle
        ]
        for _ in range(4):
            pygame.draw.line(surf, WHITE, white_vertices[0], white_vertices[1], 1) # down
            pygame.draw.line(surf, WHITE, white_vertices[1], white_vertices[2], 1) # left

            pygame.draw.line(surf, BLACK, black_vertices[0], black_vertices[1], 1) # down
            pygame.draw.line(surf, BLACK, black_vertices[2], black_vertices[3], 1) # left

            white_vertices = [self._rotate_point_90_clockwise(v) for v in white_vertices]
            black_vertices = [self._rotate_point_90_clockwise(v) for v in black_vertices]
        return surf
    
    def _rotate_point_90_clockwise(self, point: tuple[int,int]) -> tuple[int,int]:
        x, y = point

        # If this ever becomes a problem (unlikely), do vertical and vertikal flips instead.
        assert (
            self.display_config.TILE_SIZE.w == self.display_config.TILE_SIZE.h, 
            f"Can't perform a non-distorting rotation if the TILE_SIZE dimensions differ: {self.display_config.TILE_SIZE}"
        )

        c = (self.display_config.TILE_SIZE.w - 1) / 2  # geometric centre
        # translate
        x_shift, y_shift = x - c, y - c
        # rotate clockwise
        x_rot, y_rot = y_shift, -x_shift
        # translate back
        return int(x_rot + c), int(y_rot + c)

