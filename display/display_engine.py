from display.engine_protocol import EngineProtocol
from display.main_display import MainDisplay
from display.view_port import ViewPort
from game.world_state import WorldState
from loaders.tileset import ega_palette
import pygame
import animation.sprite as sprite
import animation.flames as flames

from dark_libraries.dark_math import Coord
from typing import Dict, Optional
from game.u5map import U5Map

class DisplayEngine(EngineProtocol):

    def __init__(self, world_state: WorldState):

        # Create and reference important components.
        self.view_port = ViewPort(engine=self, palette=ega_palette)
        self.main_display = MainDisplay(view_port=self.view_port)
        self.world_state = world_state

        # Set up pygame
        pygame.init()
        pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
        self.screen = pygame.display.set_mode(tuple(self.main_display.size_in_pixels()))
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Init internal state
        self.sprites: Dict[Coord, sprite.Sprite] = {}
        self.active_map: Optional[U5Map] = None
        self.active_level = 0

        # Register tile_id hooks.
        self.register_special_tiles()

    def register_special_tiles(self):

        # Flaming objects 
        for tile_id, sprite_master_copy in flames.build_all_sprites().items():
            self.view_port.register_animated_tile(tile_id, sprite_master_copy)

        # Other animated tiles
        for tile_id, sprite_master_copy in sprite.build_animated_tile_sprites().items():
            self.view_port.register_animated_tile(tile_id, sprite_master_copy)

    def register_sprite(self, sprite: sprite.Sprite) -> None:
        self.sprites[sprite.world_coord] = sprite

    def unregister_sprite(self, sprite: sprite.Sprite) -> None:
        self.sprites.pop(sprite.world_coord, None)

    def clear_sprites(self) -> None:
        self.sprites.clear()

    def set_active_map(self, u5map: U5Map, map_level: int) -> None:
        self.active_map = u5map
        self.active_level = map_level

    def render(self, player_coord: Coord):

        # Update window title with current location/world of player.
        pygame.display.set_caption(f"{self.active_map.name} [{player_coord}]")

        # Centre the viewport on the player.
        self.view_port.centre_view_on(player_coord)

        # Render current viewport from raw map data
        self.view_port.draw_map(
            self.active_map,
            self.active_level
        )

        for sprite in self.sprites.values():
            self.view_port.draw_sprite(sprite)

        # Scale for display
        scaled_surface = self.view_port.get_output_surface()
        pygame.transform.scale(
            surface = self.view_port.get_input_surface(),
            size = scaled_surface.get_size(),
            dest_surface = scaled_surface
        )

        # Blit to screen
        self.screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()