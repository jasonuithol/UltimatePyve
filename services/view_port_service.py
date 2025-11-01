from enum import Enum
import pygame

from dark_libraries.dark_math import Coord, Rect
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.magic_ray_set import MagicRaySet
from models.projectile import Projectile
from models.sprite import Sprite
from models.tile import Tile
from models.u5_glyph import U5Glyph

from services.surface_factory import SurfaceFactory
from view.display_config import DisplayConfig
from view.view_port import ViewPort

from services.view_port_data_provider import ViewPortData, ViewPortDataProvider

ActiveCursor = tuple[Coord[int], Sprite[Tile]]

BIBLICALLY_ACCURATE_PROJECTILE_OFFSET       = (0.25,  0.0)

# TODO: Assumes casting north.  OK for east/west but south will look cooked.
BIBLICALLY_ACCURATE_MAGIC_RAY_ORIGIN_OFFSET = (0.45 ,  0.0)


class ViewPortMode(Enum):
    PartyMode = 123
    CombatMode = 456

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
        self._magic_ray_set: MagicRaySet = None

    def _after_inject(self):
        self._combat_view_rect = Rect(Coord(-3,-3), self.display_config.VIEW_PORT_SIZE)

    #
    # VISUAL SFX
    #

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
        self._cursors.pop(cursor_type, None)
        self.log(f"DEBUG: Removed cursor {cursor_type}")

    #
    # All magic ray coords will be treated as TILE coords
    #
    def set_magic_rays(self, magic_ray_set: MagicRaySet):
        self._magic_ray_set = magic_ray_set

    #
    # COMBAT vs PARTY MODE
    #

    def set_combat_mode(self):
        self._set_mode(
            value = ViewPortMode.CombatMode,
            default_tile_id = 255   # Black block
        )

    def set_party_mode(self):
        self._set_mode(
            value = ViewPortMode.PartyMode,
            default_tile_id = 5     # grass 
        )

    @property
    def view_rect(self) -> Rect[int]:
        if self._mode == ViewPortMode.PartyMode:
            minimum_corner = self.party_agent.coord - (self.display_config.VIEW_PORT_SIZE // 2)
            return Rect[int](minimum_corner, self.display_config.VIEW_PORT_SIZE)
        else:
            return self._combat_view_rect            

    def render(self):

        self.view_port.clear()

        self.draw_map()

        #
        # draw overlays e.g. cursors
        #

        if self._damage_blast_coord:
            self.draw_world_tile(self._damage_blast_coord, self.global_registry.tiles.get(0))

        if self._projectile:
            self.draw_projectile()

        for active_cursor in self._cursors.values():
            cursor_coord, cursor_sprite = active_cursor
            self.draw_world_tile( 
                cursor_coord,
                cursor_sprite.get_current_frame(0.0)
            )

        if self._magic_ray_set:
            self._draw_magic_rays()

    def draw_map(self) -> None:

        if self._mode == ViewPortMode.PartyMode:
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

    def _draw_magic_rays(self):

        unscaled_origin = (self._magic_ray_set.origin - self.view_rect.minimum_corner) * self.display_config.TILE_SIZE
        biblically_accurate_unscaled_ray_origin_offset = (BIBLICALLY_ACCURATE_MAGIC_RAY_ORIGIN_OFFSET * self.display_config.TILE_SIZE)

        for end_point in self._magic_ray_set.end_points:

            #
            # Does applying biblically_accurate_unscaled_ray_origin_offset mean that its possible some lines might finish growing on or off screen ?
            # yes. 
            #
            ray_start = biblically_accurate_unscaled_ray_origin_offset + unscaled_origin
            ray_end   = biblically_accurate_unscaled_ray_origin_offset + ((end_point - self.view_rect.minimum_corner) * self.display_config.TILE_SIZE)

            self.view_port.draw_unscaled_line(
                start_coord = ray_start,
                end_coord   = ray_end,
                rgb_mapped_color = self.global_registry.colors.get(self._magic_ray_set.color)
            )

    def _set_mode(self, value: int, default_tile_id: int):
        self.log(f"Setting mode to {value}")
        self._mode = value
        self.view_port_data_provider.set_default_tile(
            self.global_registry.tiles.get(default_tile_id)
        )
