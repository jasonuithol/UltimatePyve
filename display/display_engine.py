# file: display/display_engine.py
from display.engine_protocol import EngineProtocol
from display.main_display import MainDisplay
from display.view_port import ViewPort
from game.world_state import WorldState
import pygame
import animation.sprite as sprite
import animation.flames as flames

from dark_libraries.dark_math import Coord
from typing import Dict, Optional
from game.u5map import U5Map
from loaders.tileset import TILE_ID_GRASS

class DisplayEngine(EngineProtocol):

    # Injectable Properties
    world_state: WorldState
    main_display: MainDisplay
    view_port: ViewPort
    animated_tile_factory: sprite.AnimatedTileFactory

    def _after_inject(self):

        # Set up pygame
        pygame.init()
        pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
        self.screen = pygame.display.set_mode(self.main_display.size_in_pixels().to_tuple())
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Init internal state
        self.sprites: Dict[Coord, sprite.Sprite] = {}
        self.active_map: Optional[U5Map] = None
        self.active_level = 0

        # Register tile_id hooks.
        self.register_special_tiles()

        print(f"Initialised DisplayEngine(id={hex(id(self))})")

    def register_special_tiles(self):

        # Flaming objects 
        for tile_id, sprite_master_copy in flames.build_all_sprites().items():
            self.view_port.register_animated_tile(tile_id, sprite_master_copy)

        # Other animated tiles
        for tile_id, sprite_master_copy in self.animated_tile_factory.build_animated_tile_sprites().items():
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

    def scan_for_special_tiles(self, player_coord: Coord, ):

        view_world_coord = player_coord.subtract(self.view_port.view_size_tiles.w // 2, self.view_port.view_size_tiles.h // 2)

        for y in range(self.view_port.view_size_tiles.h):
            for x in range(self.view_port.view_size_tiles.w):
                map_coord = Coord(x, y).add(view_world_coord)

                # Don't try to pull a tile from outside the source map.
                # If out of bounds, use grass tile.
                if self.active_map.is_in_bounds(map_coord):
                    tid = self.active_map.get_tile_id(self.active_level, map_coord)
                else:
                    tid = TILE_ID_GRASS

                # if the tile is animated, register a sprite
                if tid in self.view_port._animated_tiles.keys():
                    sprite_master = self.view_port._animated_tiles[tid]
                    sprite_copy = sprite_master.spawn_from_master(map_coord)

                    self.view_port.engine.register_sprite(sprite_copy)

                # if the tile is interactable, register a sprite
                interactable = self.view_port.engine.world_state.get_interactable(tid, map_coord)
                if interactable:
                    self.view_port.engine.register_sprite(interactable.create_sprite())        

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

        # Blit to screen
        self.screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()