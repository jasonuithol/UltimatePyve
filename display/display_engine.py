# file: display/display_engine.py
from typing import Optional

import pygame

from dark_libraries.dark_math import Coord

from display.main_display import MainDisplay
from display.view_port import ViewPort
import animation.sprite as sprite
from game.u5map import U5Map

class DisplayEngine:

    # Injectable Properties
    main_display: MainDisplay
    view_port: ViewPort

    def _after_inject(self):

        # Set up pygame
        pygame.init()
        pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
        self.screen = pygame.display.set_mode(self.main_display.size_in_pixels().to_tuple())
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Init internal state
        self.avatar: sprite.Sprite = None
        self.active_map: Optional[U5Map] = None
        self.active_level = 0

        print(f"Initialised DisplayEngine(id={hex(id(self))})")


    def set_avatar_sprite(self, sprite: sprite.Sprite) -> None:
        self.avatar = sprite

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

        # draw the player over the top of whatever is at it's position.
        self.view_port.draw_sprite(player_coord, self.avatar)

        # Scale for display
        scaled_surface = self.view_port.get_output_surface()

        # Blit to screen
        self.screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()