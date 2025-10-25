from pygame import Vector2
from dark_libraries.dark_math import Coord, Rect
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.agents.party_agent import PartyAgent
from models.motion import Motion
from models.sprite import Sprite
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

    def start_projectile(self, projectile: Sprite[U5Glyph], motion: Motion):

        pass

    # TODO: We have returned to view_port coords now
    def draw_map(self, tiles: dict[Coord[int], Tile]) -> None:

        self._clear()

        for coord, tile in tiles.items():
            self.draw_tile(coord, tile)

        if self._damage_blast_coord:
            self.draw_tile(self._damage_blast_coord, self.global_registry.tiles.get(0))

    @property
    def view_rect(self) -> Rect[int]:
        party_location = self.party_agent.get_current_location()
        minimum_corner = party_location.coord - self.display_config.VIEW_PORT_SIZE // 2
        return Rect[int](minimum_corner, self.display_config.VIEW_PORT_SIZE)

    def draw_tile(self, world_coord: Coord[int], tile: Tile):

        screen_coord = (world_coord - self.view_rect.minimum_corner).scale(self.display_config.TILE_SIZE)
        if tile is None:
            tile = self.global_registry.tiles.get(TILE_ID_BLACK)

        tile.blit_to_surface(
            target_surface = self.get_input_surface(), 
            pixel_offset   = screen_coord,
            inverted       = self._invert_colors
        )
