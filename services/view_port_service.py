import pygame

from dark_libraries.dark_math import Coord, Rect
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.projectile import Projectile
from models.sprite import Sprite
from models.tile import Tile
from models.u5_glyph import U5Glyph

from view.display_config import DisplayConfig
from view.view_port import ViewPort

from services.view_port_data_provider import ViewPortData, ViewPortDataProvider

ActiveCursor = tuple[Coord[int], Sprite[Tile]]

BIBLICALLY_ACCURATE_PROJECTILE_OFFSET = 0.25,0

PARTY_MODE  = 123
COMBAT_MODE = 456

class ViewPortService(LoggerMixin):

    # Injectable Properties
    display_config: DisplayConfig
    global_registry: GlobalRegistry
    party_agent: PartyAgent
    view_port: ViewPort
    view_port_data_provider: ViewPortDataProvider

    def __init__(self):
        LoggerMixin.__init__(self)
        self.invert_colors(False)
        self.set_damage_blast_at(None)
        self._projectile: Projectile = None

        self._cursors = dict[int, ActiveCursor]()
        self._mode: int = None

    def _after_inject(self):
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

    def set_combat_mode(self):
        self._set_mode(
            value = COMBAT_MODE,
            default_tile_id = 255   # Black block
        )

    def set_party_mode(self):
        self._set_mode(
            value = PARTY_MODE,
            default_tile_id = 5     # grass 
        )

    @property
    def view_rect(self) -> Rect[int]:
        if self._mode == PARTY_MODE:
            minimum_corner = self.party_agent.coord - (self.display_config.VIEW_PORT_SIZE // 2)
            return Rect[int](minimum_corner, self.display_config.VIEW_PORT_SIZE)
        else:
            return self._combat_view_rect            

    def render(self):

        self.view_port.clear()

        self.draw_map()

        if self._damage_blast_coord:
            self.draw_world_tile(self._damage_blast_coord, self.global_registry.tiles.get(0))

        #
        # TODO: Move into ViewportService ?
        #

        if self._projectile:
            self.draw_projectile()

        # draw overlays e.g. cursors
        for active_cursor in self._cursors.values():
            cursor_coord, cursor_sprite = active_cursor
            self.draw_world_tile( 
                cursor_coord,
                cursor_sprite.get_current_frame(0.0)
            )

    def draw_map(self) -> None:

        if self._mode == PARTY_MODE:
            view_port_data: ViewPortData = self.view_port_data_provider.get_party_map_data(self.view_rect)
        else:
            view_port_data: ViewPortData = self.view_port_data_provider.get_combat_map_data(self.view_rect)
            
        for world_coord in self.view_rect:
            tile = view_port_data[world_coord]
            self.draw_world_tile(world_coord, tile)

    def draw_world_tile(self, world_coord: Coord[int], tile: Tile):
        view_coord = world_coord - self.view_rect.minimum_corner
        self.view_port.draw_tile_to_view_coord(view_coord, tile, self._invert_colors)

    def draw_projectile(self):
        # Coords are in unscaled pixels.
        current_ticks = pygame.time.get_ticks()

        if self._projectile.can_stop() == True:
            self.log(f"DEBUG: Terminating projectile {self._projectile} at {current_ticks}")
            self._projectile = None
        else:
            glyph = self._projectile.sprite.get_current_frame(current_ticks)
            projectile_world_coord = self._projectile.get_current_position()
            projectile_unscaled_pixel_coord =  (projectile_world_coord - self.view_rect.minimum_corner + BIBLICALLY_ACCURATE_PROJECTILE_OFFSET) * self.display_config.TILE_SIZE 
            self.view_port.draw_object_at_unscaled_coord(projectile_unscaled_pixel_coord, glyph, self._invert_colors)

    def _set_mode(self, value: int, default_tile_id: int):
        self.log(f"Setting mode to {value}")
        self._mode = value
        self.view_port_data_provider.set_default_tile(
            self.global_registry.tiles.get(default_tile_id)
        )
