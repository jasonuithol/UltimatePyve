import pygame
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass, field

from display.engine_protocol import EngineProtocol
import animation.sprite as sprite
from game.u5map import U5Map

from loaders.tileset import TILE_ID_GRASS, Tile
from dark_libraries.dark_math import Coord, Size

@dataclass
class ViewPort:
    engine: EngineProtocol
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

    def draw_map(self, u5map: U5Map, level_ix: int = 0) -> None:
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
                    sprite_master = self._animated_tiles[tid]
                    sprite_copy = sprite_master.spawn_from_master(map_coord)

                    self.engine.register_sprite(sprite_copy)

                interactable = self.engine.world_state.get_interactable(tid, map_coord)
                if interactable:
                    self.engine.register_sprite(interactable.create_sprite())

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

    '''
    def flood_fill_visibility(start_x, start_y, is_blocked, mark_visible):
        #            start_x, start_y: starting tile coordinates (player position)
        #            is_blocked(x, y) -> bool: True if tile blocks vision
        #            mark_visible(x, y): called for each visible tile
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
    '''