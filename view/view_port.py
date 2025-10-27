import pygame

from dark_libraries.dark_math import Coord, Rect
from dark_libraries.dark_surface import DarkSurface
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

#from models.agents.party_agent import PartyAgent
from models.agents.party_agent import PartyAgent
from models.projectile import Projectile
from models.sprite import Sprite
from models.tile import Tile
from models.u5_glyph import U5Glyph

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

ActiveCursor = tuple[Coord[int], Sprite[Tile]]

BIBLICALLY_ACCURATE_PROJECILE_OFFSET = 3.25,3

PARTY_MODE  = 123
COMBAT_MODE = 456

class ViewPort(ScalableComponent, LoggerMixin):

    # Injectable Properties
    display_config: DisplayConfig
    global_registry: GlobalRegistry
    party_agent: PartyAgent

    def __init__(self):
        LoggerMixin.__init__(self)
        self.invert_colors(False)
        self.set_damage_blast_at(None)
        self._projectile: Projectile = None

        self._cursors = dict[int, ActiveCursor]()
        self._default_tile: Tile = None
        self._mode: int = None

    def _after_inject(self):
        ScalableComponent.__init__(
            self,
            unscaled_size_in_pixels = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )
        super()._after_inject()
        self._combat_view_rect = Rect(Coord(-3,-3), self.display_config.VIEW_PORT_SIZE)

    def invert_colors(self, value: bool):
        self.log(f"Invert colors: {value}")
        self._invert_colors = value

    def set_damage_blast_at(self, coord: Coord[int]):
        self._damage_blast_coord = coord

    def start_projectile(self, projectile: Projectile[U5Glyph]):
        self._projectile = projectile
        self.log(f"DEBUG: Starting projectile={projectile}")

    def set_cursor(self, cursor_type: int, cursor_coord: Coord[int], cursor_sprite: Sprite[Tile]):
        assert not cursor_coord is None, "cursor_coord cannot be None"
        assert not cursor_sprite is None, "cursor_sprite cannot be None"
        self._cursors[cursor_type] = (cursor_coord, cursor_sprite)
        self.log(f"DEBUG: Set cursor ({cursor_type}) to {cursor_coord}")

    def remove_cursor(self, cursor_type: int):
        del self._cursors[cursor_type]
        self.log(f"DEBUG: Removed cursor {cursor_type}")

    def set_default_tile(self, tile: Tile):
        self._default_tile = tile

    def set_mode(self, value: int):
        self.log(f"Setting mode to {value}")
        self._mode = value

    @property
    def view_rect(self) -> Rect[int]:
        if self._mode == PARTY_MODE:
            #
            # TODO: Use a Viewport Service
            #
            minimum_corner = self.party_agent.coord - (self.display_config.VIEW_PORT_SIZE // 2)
            return Rect[int](minimum_corner, self.display_config.VIEW_PORT_SIZE)
        else:
            return self._combat_view_rect            

    # TODO: We have returned to view_port coords now
    def draw_map(self, tiles: dict[Coord[int], Tile]) -> None:

        self._clear()

        for coord, tile in tiles.items():
            self.draw_tile(coord, tile)

        if self._damage_blast_coord:
            self.draw_tile(self._damage_blast_coord, self.global_registry.tiles.get(0))

        #
        # TODO: Move into ViewportService ?
        #

        if self._projectile:
            # Coords are in unscaled pixels.
            current_ticks = pygame.time.get_ticks()
            glyph = self._projectile.sprite.get_current_frame(current_ticks)
            projectile_world_coord = self._projectile.get_current_position()

            if self._projectile.can_stop() == True:
                self.log(f"DEBUG: Terminating projectile {self._projectile} at {current_ticks}")
                self._projectile = None
            else:
                projectile_unscaled_pixel_coord = (projectile_world_coord + BIBLICALLY_ACCURATE_PROJECILE_OFFSET) * self.display_config.TILE_SIZE 
#                print(f"BILL ODDIE: projectile_world_coord={projectile_world_coord}, projectile_unscaled_pixel_coord={projectile_unscaled_pixel_coord}")
                self.draw_object_at_unscaled_coord(projectile_unscaled_pixel_coord, glyph)
#                self.draw_object_at_unscaled_coord(projectile_unscaled_pixel_coord, self.global_registry.tiles.get(0))

        #
        # TODO: Move into ViewportService ?
        #

        # draw overlays e.g. cursors
        for active_cursor in self._cursors.values():
            cursor_coord, cursor_sprite = active_cursor
            self.draw_tile( 
                cursor_coord,
                cursor_sprite.get_current_frame(0.0)
            )


    def draw_tile(self, world_coord: Coord[int], tile: Tile):

        if tile is None:
            tile = self._default_tile

        unscaled_pixel_coord = (world_coord - self.view_rect.minimum_corner).scale(self.display_config.TILE_SIZE)
        self.draw_object_at_unscaled_coord(unscaled_pixel_coord, tile)

    def draw_object_at_unscaled_coord(self, unscaled_pixel_coord: Coord[int], dark_surface: DarkSurface):

        dark_surface.blit_to_surface(
            target_surface = self.get_input_surface(), 
            pixel_offset   = unscaled_pixel_coord,
            inverted       = self._invert_colors
        )
