# file: display/display_engine.py
import pygame

from dark_libraries.dark_math import Coord

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.u5_map import U5Map
from services.map_cache.map_cache_service import MapCacheService
from services.map_cache.map_level_contents import MapLevelContents
from models.sprite import Sprite
from models.tile   import Tile

from services.world_clock import WorldClock

from view.display_config      import DisplayConfig
from view.interactive_console import InteractiveConsole
from view.view_port           import ViewPort
from view.main_display        import MainDisplay

class DisplayController(LoggerMixin):

    # Injectable
    display_config:      DisplayConfig
    main_display:        MainDisplay
    view_port:           ViewPort
    interactive_console: InteractiveConsole

    # Map generation
    global_registry: GlobalRegistry
    map_cache_service: MapCacheService
    world_clock: WorldClock

    def init(self):

        self.main_display.init()

        self.screen = pygame.display.set_mode(
            size  = self.main_display.scaled_size().to_tuple(),
            flags = pygame.SCALED | pygame.DOUBLEBUF, 
            vsync = 1
        )
        self.clock = pygame.time.Clock()

        # Init internal state
        self.avatar: Sprite = None
        self.active_location_index: int = None
        self.active_level_index: int = None
        self.active_map: U5Map = None

        self.log(f"Initialised {__class__.__name__}(id={hex(id(self))})")

    def _get_map_tiles(self) -> dict[Coord, Tile]:
        map_level_contents: MapLevelContents = self.map_cache_service.get_map_level_contents(
            self.active_location_index,
            self.active_level_index
        )

        return {
            world_coord:
            map_level_contents.get_coord_contents(world_coord).get_renderable_frame()
            for world_coord in self.view_port.view_rect
        }
    
    def set_avatar_sprite(self, sprite: Sprite):
        self.avatar = sprite

    def set_active_map(self, location_index: int, level_index: int):
        self.active_location_index = location_index
        self.active_level_index = level_index
        self.active_map = self.global_registry.maps.get(location_index)

    #
    # TODO: Most of this is ViewPort logic.  Fix
    #       The rest contains visual composition logic, move to MainDisplay
    #
    def render(self, player_coord: Coord):

        # Update window title with current location/world of player.
        pygame.display.set_caption(
            f"{self.active_map.location_metadata.name} [{player_coord}]" 
            +
            f" fps={int(self.clock.get_fps())}"
            +
            f" time={self.world_clock.get_daylight_savings_time()}"
        )

        scaled_border_thiccness = self.display_config.FONT_SIZE.w * self.display_config.SCALE_FACTOR

        #
        # Main Display
        #
        self.main_display.draw()
        md_scaled_surface = self.main_display.get_output_surface()
        md_scaled_pixel_offset = (0,0)
        self.screen.blit(md_scaled_surface, md_scaled_pixel_offset)

        #
        # ViewPort
        #

        # Centre the viewport on the player.
        self.view_port.centre_view_on(player_coord)

        # Render current viewport from populated map data.
        map_tiles = self._get_map_tiles()
        self.view_port.draw_map(map_tiles)

        # draw the player over the top of whatever is at it's position.
        avatar_tile = self.avatar.get_current_frame_tile()
        self.view_port.draw_tile(player_coord, avatar_tile)

        vp_scaled_surface = self.view_port.get_output_surface()
        vp_scaled_pixel_offset = (scaled_border_thiccness, scaled_border_thiccness)
        self.screen.blit(vp_scaled_surface, vp_scaled_pixel_offset)

        #
        # InteractiveConsole
        #
        ic_scaled_surface = self.interactive_console.get_output_surface()
        ic_scaled_pixel_offset = (
            vp_scaled_surface.get_width() + scaled_border_thiccness * 2, 
            vp_scaled_surface.get_height() - ic_scaled_surface.get_height()
        )
        self.screen.blit(ic_scaled_surface, ic_scaled_pixel_offset)

        pygame.display.flip()

        # allow reporting of FPS
        self.clock.tick()
