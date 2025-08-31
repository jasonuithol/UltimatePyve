import pygame
from copy import copy
from typing import Any, Tuple, List, Optional, Dict
from dataclasses import dataclass, field
from collections import deque

import flames
import terrain
from u5map import U5Map
import sprite

from loaders.tileset import ega_palette, TILE_ID_GRASS, Tile
from dark_math import Coord, Size



'''
def tile_to_surface(tile_data: TileData, surf: pygame.Surface, pixel_offset: Coord) -> None:
    for y, row in enumerate(tile_data):
        for x, pix in enumerate(row):
            surf.set_at((x + pixel_offset.x, y + pixel_offset.y), ega_palette[pix])
'''

@dataclass
class ViewPort:
    engine: Any
    palette: List[Tuple[int,int,int]]
    view_world_coord: Coord = field(default_factory=lambda: Coord(0, 0))
    view_size_tiles: Size = field(default_factory=lambda: Size(21, 15))
    tile_size_pixels: int = 16
    display_scale: int = 2
    _unscaled_surface: Optional[pygame.Surface] = None
    _scaled_surface: Optional[pygame.Surface] = None
    _animated_tiles: Dict[int, sprite.Sprite] = field(default_factory=dict)

    def view_size_in_pixels(self) -> Size:
         return self.view_size_tiles.scale(self.tile_size_pixels)
    
    def view_size_in_pixels_scaled(self) -> Size:
         return self.view_size_in_pixels().scale(self.display_scale)

    def set_display_scale(self, s: int) -> None:
         self.display_scale = s

    def register_animated_tile(self, tile_id: int, sprite_master: sprite.Sprite) -> None:
        self._animated_tiles[tile_id] = sprite_master

    def centre_view_on(self, world_coords: Coord) -> None:
        offset = Coord(self.view_size_tiles.w // 2, self.view_size_tiles.h // 2)
        self.view_world_coord = world_coords.subtract(offset)

    def get_input_surface(self) -> pygame.Surface:
        if self._unscaled_surface is None:
            self._unscaled_surface = pygame.Surface(tuple(self.view_size_in_pixels()))
        return self._unscaled_surface

    def get_output_surface(self) -> pygame.Surface:
        if self._scaled_surface is None:
            self._scaled_surface = pygame.Surface(tuple(self.view_size_in_pixels_scaled()))
        return self._scaled_surface

    def flood_fill_visibility(start_x, start_y, is_blocked, mark_visible):
        """
        Ultima V–style boundary-fill for visibility.

        Args:
            start_x, start_y: starting tile coordinates (player position)
            is_blocked(x, y) -> bool: True if tile blocks vision
            mark_visible(x, y): called for each visible tile
        """
        visited = set()
        q = deque()
        q.append((start_x, start_y))
        visited.add((start_x, start_y))

        while q:
            x, y = q.popleft()
            mark_visible(x, y)

            # 4-way expansion
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in visited:
                    continue
                if is_blocked(nx, ny):
                    continue
                visited.add((nx, ny))
                q.append((nx, ny))

    def draw_map(self, u5map: U5Map, level_ix: int = 0) -> None:
        """
        Render the map or a subsection of it to a Pygame Surface.
        rect: (tile_x, tile_y, tile_w, tile_h) in tile coordinates.
        """
        viewport_surface = self.get_input_surface()

        for y in range(self.view_size_tiles.h):
            for x in range(self.view_size_tiles.w):
                map_coord = Coord(x, y).add(self.view_world_coord)

                # Don't try to pull a tile from outside the source map.
                # If out of bounds, use grass tile.
                if map_coord.is_in_bounds(u5map.size_in_tiles):
                    tid = u5map.get_tile_id(level_ix, map_coord.x, map_coord.y)
                else:
                    tid = TILE_ID_GRASS

                # if the tile is animated, register a sprite
                if tid in self._animated_tiles.keys():
                    sprite_copy = copy(self._animated_tiles[tid])
                    sprite_copy.world_coord = map_coord
                    random_number = ((hash(tuple(map_coord)) & 0xFFFFFFFFFFFFFFFF) / float(1 << 64))
                    sprite_copy.frame_time_offset = sprite_copy.frame_time * len(sprite_copy.frames) * random_number

                    self.engine.register_sprite(sprite_copy)

                # Don't try to render a non-existant tile id.
                if 0 <= tid < len(u5map.tileset):
                    tile: Tile = u5map.tileset[tid]
                    tile.blit_to_surface(
                        viewport_surface, 
                        Coord(x * self.tile_size_pixels, y * self.tile_size_pixels)
                    )
                else:
                    print(f"Warning: tile id {tid!r} out of range, skipping render.")

    def draw_sprite(self, sprite: sprite.Sprite) -> None:

        """
        Draw a sprite to the Viewport
        """
        # Determine screen position
        screen_coord = sprite.world_coord.subtract(self.view_world_coord).scale(self.tile_size_pixels)

        # Get the current animation frame tile.
        ticks = pygame.time.get_ticks()
        frame_tile = sprite.get_current_frame_tile(ticks)

        # Draw
        frame_tile.blit_to_surface(
            target_surface = self.get_input_surface(),
            pixel_offset = tuple(screen_coord)
        )


@dataclass 
class MainDisplay:
    view_port: ViewPort

    def size_in_pixels(self) -> Size:
         return self.view_port.view_size_in_pixels_scaled()

# file: engine.py
class DisplayEngine:

    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
        view_port = ViewPort(engine=self, palette=ega_palette)
        self.main_display = MainDisplay(view_port)
        self.screen = pygame.display.set_mode(tuple(self.main_display.size_in_pixels()))
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.sprites: Dict[Coord, Sprite] = {}
        self.active_map: Optional[U5Map] = None
        self.active_level = 0

        # Flaming objects 
        for tile_id, sprite_master_copy in flames.build_all_sprites().items():
            view_port.register_animated_tile(tile_id, sprite_master_copy)

        # Other animated tiles
        for tile_id, sprite_master_copy in sprite.build_animated_tile_sprites().items():
            view_port.register_animated_tile(tile_id, sprite_master_copy)

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
        self.main_display.view_port.centre_view_on(player_coord)

        # Render current viewport from raw map data
        self.main_display.view_port.draw_map(
            self.active_map,
            self.active_level
        )

        for sprite in self.sprites.values():
            self.main_display.view_port.draw_sprite(sprite)

        # Scale for display
        scaled_surface = self.main_display.view_port.get_output_surface()
        pygame.transform.scale(
            surface = self.main_display.view_port.get_input_surface(),
            size = scaled_surface.get_size(),
            dest_surface = scaled_surface
        )

        # Blit to screen
        self.screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()
