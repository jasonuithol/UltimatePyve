import pygame
from dark_libraries.dark_math import Coord, Rect
from dark_libraries.dark_surface import DarkSurface
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.agents.party_agent import PartyAgent
from models.projectile import Projectile
from models.tile import Tile, TILE_ID_BLACK
from models.u5_glyph import U5Glyph

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

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
        self._window: Rect = None

    def _after_inject(self):
        ScalableComponent.__init__(
            self,
            unscaled_size_in_pixels = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )

    def invert_colors(self, value: bool):
        self.log(f"Invert colors: {value}")
        self._invert_colors = value

    def set_damage_blast_at(self, coord: Coord[int]):
        self._damage_blast_coord = coord

    def start_projectile(self, projectile: Projectile[U5Glyph]):
        self._projectile = projectile
        self.log(f"DEBUG: Starting projectile={projectile}")

    # TODO: We have returned to view_port coords now
    def draw_map(self, tiles: dict[Coord[int], Tile]) -> None:

        self._clear()

        for coord, tile in tiles.items():
            self.draw_tile(coord, tile)

        if self._damage_blast_coord:
            self.draw_tile(self._damage_blast_coord, self.global_registry.tiles.get(0))

        #
        # TODO: Really should be managing SOME of this in SfxLibraryService
        #
        if self._projectile:
            # Coords are in unscaled pixels.
            current_ticks = pygame.time.get_ticks()

            if self._projectile.can_stop() == True:
                self.log(f"DEBUG: Terminating projectile {self._projectile} at {current_ticks}")
                self._projectile = None
            else:
                projectile_coord_float = self._projectile.get_current_position()
                glyph = self._projectile.sprite.get_current_frame(current_ticks)
                print(f"BILL ODDIE: {projectile_coord_float}")
                self.draw_projectile(projectile_coord_float, glyph)

    # set's the rectangle, in world coords, that this viewport represents in the wider set of world co-ordinates.
    def set_window(self, window: Rect):
        assert (
            window.size * self.display_config.TILE_SIZE == self.get_input_surface().get_size(),
            "This window rect's size, once accounting for TILE_SIZE, does not match the actual surface size of this component: "
            +
            f"window.size * self.display_config.TILE_SIZE = {window.size * self.display_config.TILE_SIZE}, "
            +
            f"self.get_input_surface().get_size() = {self.get_input_surface().get_size()}"
        )
        self.log(f"DEBUG: Setting view_port window to {window}")
        self._window = window

    @property
    def window(self) -> Rect:
        return self._window

    def draw_tile(self, world_coord: Coord[int], tile: Tile):

        if tile is None:
            tile = self.global_registry.tiles.get(TILE_ID_BLACK)

        unscaled_pixel_coord = (world_coord - self.window.minimum_corner).scale(self.display_config.TILE_SIZE)
        self.draw_object_at_unscaled_coord(unscaled_pixel_coord, tile)

    def draw_projectile(self, world_coord_float: Coord[float], glyph: U5Glyph):

        unscaled_pixel_coord = (world_coord_float - self.window.minimum_corner).scale(self.display_config.FONT_SIZE)
        self.draw_object_at_unscaled_coord(unscaled_pixel_coord, glyph)

    def draw_object_at_unscaled_coord(self, unscaled_pixel_coord: Coord[int], dark_surface: DarkSurface):

        dark_surface.blit_to_surface(
            target_surface = self.get_input_surface(), 
            pixel_offset   = unscaled_pixel_coord,
            inverted       = self._invert_colors
        )
