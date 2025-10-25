# file: display/display_engine.py
import pygame

from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.npc_agent import NpcAgent
from models.agents.party_agent import PartyAgent
from models.sprite import Sprite
from models.tile   import Tile
from models.u5_map import U5Map

from view.display_config      import DisplayConfig
from view.info_panel import InfoPanel
from view.interactive_console import InteractiveConsole
from view.view_port           import ViewPort
from view.main_display        import MainDisplay

from services.field_of_view_calculator import FieldOfViewCalculator
from services.lighting_service import LightingService
from services.map_cache.map_cache_service import MapCacheService
from services.map_cache.map_level_contents import MapLevelContents
from services.npc_service import NpcService
from services.world_clock import WorldClock

class DisplayService(LoggerMixin):

    # Injectable
    display_config:      DisplayConfig
    main_display:        MainDisplay
    view_port:           ViewPort
    info_panel:          InfoPanel
    interactive_console: InteractiveConsole

    # Map generation
    global_registry:   GlobalRegistry
    map_cache_service: MapCacheService
    world_clock:       WorldClock
    fov_calculator:    FieldOfViewCalculator
    lighting_service:  LightingService
    npc_service:       NpcService

    party_agent: PartyAgent

    def init(self):

        self.screen = pygame.display.set_mode(
            size  = self.main_display.scaled_size().to_tuple(),
            flags = pygame.SCALED | pygame.DOUBLEBUF, 
            vsync = 1
        )
        self.clock = pygame.time.Clock()
        self._cursors = dict[int, tuple[Coord[int], Sprite[Tile]]]()

        self.log(f"Initialised {__class__.__name__}(id={hex(id(self))})")

    def set_cursor(self, cursor_type: int, cursor_coord: Coord[int], cursor_sprite: Sprite[Tile]):
        assert not cursor_coord is None, "cursor_coord cannot be None"
        assert not cursor_sprite is None, "cursor_sprite cannot be None"
        self._cursors[cursor_type] = (cursor_coord, cursor_sprite)
        self.log(f"DEBUG: Set cursor ({cursor_type}) to {cursor_coord}")

    def remove_cursor(self, cursor_type: int):
        del self._cursors[cursor_type]
        self.log(f"DEBUG: Removed cursor {cursor_type}")

    #
    # TODO: move to ViewPortDataProvider
    #
    def _get_map_tiles(self) -> dict[Coord[int], Tile]:

        player_location = self.party_agent.get_current_location()

        map_level_contents: MapLevelContents = self.map_cache_service.get_map_level_contents(
            player_location.location_index,
            player_location.level_index
        )

        visible_coords = self.fov_calculator.calculate_fov_visibility(
            player_location,
            self.view_port.view_rect
        )

        lit_coords = self.lighting_service.calculate_lighting(
            player_location,
            self.lighting_service.get_player_light_radius(),
            visible_coords
        )

        npcs = self.npc_service.get_npcs()
        assert len(npcs) > 0, "Must have at least 1 NPC (the player) to draw"

        def get_frame(world_coord: Coord[int]) -> Tile:
            if not world_coord in visible_coords.intersection(lit_coords):
                return None
            npc: NpcAgent = npcs.get(world_coord, None)
            if not npc is None:
                return npc.current_tile
            interactable = self.global_registry.interactables.get(world_coord)
            if not interactable is None:
                return self.global_registry.tiles.get(interactable.get_current_tile_id())
            return map_level_contents.get_coord_contents(world_coord).get_renderable_frame()
        
        return {
            world_coord:
            get_frame(world_coord)
            for world_coord in self.view_port.view_rect
        }

    def render(self):

        party_location = self.party_agent.get_current_location()
        active_map: U5Map = self.global_registry.maps.get(party_location.location_index)

        # Update window title with current location/world of player.
        pygame.display.set_caption(
            f"{active_map.name} [{party_location.coord}]" 
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

        # Render current viewport from populated map data.
        map_tiles = self._get_map_tiles()
        self.view_port.draw_map(map_tiles)

        # draw overlays e.g. cursors
        for cursor_coord_sprite_tuple in self._cursors.values():
            cursor_coord, cursor_sprite = cursor_coord_sprite_tuple
            self.view_port.draw_tile( 
                cursor_coord,
                cursor_sprite.get_current_frame(0.0)
            )

        vp_scaled_surface = self.view_port.get_output_surface()
        vp_scaled_pixel_offset = (scaled_border_thiccness, scaled_border_thiccness)
        self.screen.blit(vp_scaled_surface, vp_scaled_pixel_offset)



        right_hand_element_x = vp_scaled_surface.get_width() + scaled_border_thiccness * 2

        #
        # InfoPanel
        #
        self.info_panel.draw()

        ip_scaled_surface = self.info_panel.get_output_surface()
        ip_scaled_pixel_offset = (
            right_hand_element_x, 
            0
        )
        self.screen.blit(ip_scaled_surface, ip_scaled_pixel_offset)


        #
        # InteractiveConsole
        #
        self.interactive_console.draw()

        ic_scaled_surface = self.interactive_console.get_output_surface()
        ic_scaled_pixel_offset = (
            right_hand_element_x, 
            self.main_display.scaled_size().h - self.interactive_console.scaled_size().h - scaled_border_thiccness
        )
        self.screen.blit(ic_scaled_surface, ic_scaled_pixel_offset)

        pygame.display.flip()

        # allow reporting of FPS
        self.clock.tick()
