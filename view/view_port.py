from dark_libraries.dark_math import Coord, Rect
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.party_state import PartyState
from models.tile import Tile, TILE_ID_BLACK

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

class ViewPort(ScalableComponent, LoggerMixin):

    # Injectable Properties
    display_config: DisplayConfig
    global_registry: GlobalRegistry
    party_state: PartyState

    def __init__(self):
        LoggerMixin.__init__(self)

    def _after_inject(self):
        ScalableComponent.__init__(
            self,
            unscaled_size_in_pixels = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )

    # TODO: We have returned to view_port coords now
    def draw_map(self, tiles: dict[Coord, Tile]) -> None:

        self._clear()

        for coord, tile in tiles.items():
            self.draw_tile(coord, tile)

    @property
    def view_rect(self) -> Rect:
        party_location = self.party_state.get_current_location()
        minimum_corner = party_location.coord - self.display_config.VIEW_PORT_SIZE // 2
        return Rect(minimum_corner, self.display_config.VIEW_PORT_SIZE)

    def draw_tile(self, world_coord: Coord, tile: Tile):

        screen_coord = (world_coord - self.view_rect.minimum_corner).scale(self.display_config.TILE_SIZE)
        if tile is None:
            tile = self.global_registry.tiles.get(TILE_ID_BLACK)
        tile.blit_to_surface(
            self.get_input_surface(), 
            screen_coord
        )
