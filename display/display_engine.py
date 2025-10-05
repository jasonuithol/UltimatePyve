# file: display/display_engine.py
import pygame

from dark_libraries.dark_math import Coord

from animation.sprite import Sprite
from game.map_content.map_content_registry import MapContentRegistry
from game.world_clock import WorldClock
from maps.u5map       import U5Map

from .display_config      import DisplayConfig
from .interactive_console import InteractiveConsole
from .tileset             import Tile
from .view_port           import ViewPort
from .main_display        import MainDisplay

class DisplayEngine:

    # Injectable
    display_config:      DisplayConfig
    main_display:        MainDisplay
    view_port:           ViewPort
    interactive_console: InteractiveConsole

    # Map generation
    map_content_registry: MapContentRegistry
    world_clock: WorldClock

    def init(self):

        # Set up pygame
        pygame.init()
        pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

        self.screen = pygame.display.set_mode(
            size  = self.main_display.scaled_size().to_tuple(),
            flags = pygame.SCALED | pygame.DOUBLEBUF, 
            vsync = 1
        )
        self.clock = pygame.time.Clock()

        # Init internal state
        self.avatar: Sprite = None
        self.active_map: U5Map = None
        self.active_level = 0

        print(f"Initialised DisplayEngine(id={hex(id(self))})")

    def _get_map_tiles(self) -> dict[Coord, Tile]:
        return {
            world_coord:
            self.map_content_registry.get_coord_contents(
                location_index = self.active_map.location_metadata.location_index,
                level_index = self.active_level,
                coord = world_coord
            ).get_renderable_frame()
            for world_coord in self.view_port.view_rect
        }
    
    def set_avatar_sprite(self, sprite: Sprite):
        self.avatar = sprite

    def set_active_map(self, u5map: U5Map, map_level: int):
        self.active_map = u5map
        self.active_level = map_level

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
