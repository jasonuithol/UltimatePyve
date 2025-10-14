# file: display/display_engine.py
import pygame

from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.party_member_agent import PartyMemberAgent
from models.party_state import PartyState
from models.tile   import Tile
from models.u5_map import U5Map

from services.avatar_sprite_factory import AvatarSpriteFactory
from view.display_config      import DisplayConfig
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
    interactive_console: InteractiveConsole

    # Map generation
    global_registry:   GlobalRegistry
    map_cache_service: MapCacheService
    world_clock:       WorldClock
    fov_calculator:    FieldOfViewCalculator
    lighting_service:  LightingService
    npc_service:       NpcService
    avatar_sprite_factory: AvatarSpriteFactory

    party_state: PartyState

    def init(self):

        self.main_display.init()

        self.screen = pygame.display.set_mode(
            size  = self.main_display.scaled_size().to_tuple(),
            flags = pygame.SCALED | pygame.DOUBLEBUF, 
            vsync = 1
        )
        self.clock = pygame.time.Clock()

        self.set_party_mode()

        self.log(f"Initialised {__class__.__name__}(id={hex(id(self))})")


    def _get_map_tiles(self) -> dict[Coord, Tile]:

        player_location = self.party_state.get_current_location()

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

        def get_frame(world_coord: Coord) -> Tile:
            if not world_coord in visible_coords.intersection(lit_coords):
                return None
            npc = npcs.get(world_coord, None)
            if not npc is None:
                return npc.sprite.get_current_frame_tile()
            interactable = self.global_registry.interactables.get(world_coord)
            if not interactable is None:
                return self.global_registry.tiles.get(interactable.get_current_tile_id())
            return map_level_contents.get_coord_contents(world_coord).get_renderable_frame()
        
        return {
            world_coord:
            get_frame(world_coord)
            for world_coord in self.view_port.view_rect
        }

    def set_party_mode(self):
        self.party_mode = True
        self.combat_mode = False
        self.party_member_agents: list[PartyMemberAgent] = None

    def set_combat_mode(self, party_member_agents: list[PartyMemberAgent]):
        self.party_mode = False
        self.combat_mode = True
        self.party_member_agents = party_member_agents

    #
    # TODO: remove player_coord as a parameter and add it to the state
    #
    def render(self):

        party_location = self.party_state.get_current_location()
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

        if self.party_mode:
            # draw the player over the top of whatever is at it's position.
            transport_mode, transport_direction = self.party_state.get_transport_state()
            avatar_sprite = self.avatar_sprite_factory.create_player(transport_mode, transport_direction)

            avatar_tile = avatar_sprite.get_current_frame_tile()
            self.view_port.draw_tile(party_location.coord, avatar_tile)

        elif self.combat_mode:
            for party_member_agent in self.party_member_agents:
                self.view_port.draw_tile(party_member_agent.global_location.coord, party_member_agent.sprite.get_current_frame_tile())

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
