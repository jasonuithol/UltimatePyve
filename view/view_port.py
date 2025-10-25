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

    def _after_inject(self):
        ScalableComponent.__init__(
            self,
            unscaled_size_in_pixels = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )
        super()._after_inject()

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
            glyph = self._projectile.sprite.get_current_frame(current_ticks)
            projectile_coord = self._projectile.get_current_position()

            if self._projectile.can_stop() == True:
                self.log(f"DEBUG: Terminating projectile {self._projectile} at {current_ticks}")
                self._projectile = None
            else:
                print(f"BILL ODDIE: {projectile_coord}")
#                self.draw_object_at_unscaled_coord(projectile_coord, glyph)
                self.draw_object_at_unscaled_coord(projectile_coord, self.global_registry.tiles.get(TILE_ID_BLACK))

    @property
    def view_rect(self) -> Rect[int]:
        party_location = self.party_agent.get_current_location()
        minimum_corner = party_location.coord - self.display_config.VIEW_PORT_SIZE // 2
        return Rect[int](minimum_corner, self.display_config.VIEW_PORT_SIZE)

    def draw_tile(self, world_coord: Coord[int], tile: Tile):

        if tile is None:
            tile = self.global_registry.tiles.get(TILE_ID_BLACK)

        unscaled_pixel_coord = (world_coord - self.view_rect.minimum_corner).scale(self.display_config.TILE_SIZE)
        self.draw_object_at_unscaled_coord(unscaled_pixel_coord, tile)

    def draw_object_at_unscaled_coord(self, unscaled_pixel_coord: Coord[int], dark_surface: DarkSurface):

        dark_surface.blit_to_surface(
            target_surface = self.get_input_surface(), 
            pixel_offset   = unscaled_pixel_coord,
            inverted       = self._invert_colors
        )
