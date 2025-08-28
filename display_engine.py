import pygame
from typing import Tuple, List, Optional, Self
from dataclasses import dataclass, field

from u5map import U5Map
from sprite import Sprite
from loaders.tileset import ega_palette, TILE_ID_GRASS

@dataclass
class Vector2:
    x: int
    y: int

    def scale(self, s: int) -> Self:
         return self.__class__(self.x * s, self.y * s)
    
    def add(self, other: Self) -> Self:
            return self.__class__(self.x + other.x, self.y + other.y)

    def subtract(self, other: Self) -> Self:
            return self.__class__(self.x - other.x, self.y - other.y)

    # allow tuple(Size) to yield (x,y)
    def __iter__(self):
        yield self.x
        yield self.y

@dataclass
class Size(Vector2):
    @property
    def w(self) -> int:
        return self.x

    @w.setter
    def w(self, value: int):
        self.x = value

    @property
    def h(self) -> int:
        return self.y

    @h.setter
    def h(self, value: int):
        self.y = value

@dataclass
class Coord(Vector2):
    pass

    def is_in_bounds(self, size: Size) -> bool:
        return 0 <= self.x < size.w and 0 <= self.y < size.h

@dataclass
class ViewPort:
    palette: List[Tuple[int,int,int]]
    view_world_coord: Coord = field(default_factory=lambda: Coord(0, 0))
    view_size_tiles: Size = field(default_factory=lambda: Size(21, 15))
    tile_size_pixels: int = 16
    display_scale: int = 2
    _unscaled_surface: Optional[pygame.Surface] = None
    _scaled_surface: Optional[pygame.Surface] = None

    def view_size_in_pixels(self) -> Size:
         return self.view_size_tiles.scale(self.tile_size_pixels)
    
    def view_size_in_pixels_scaled(self) -> Size:
         return self.view_size_in_pixels().scale(self.display_scale)

    def set_display_scale(self, s: int):
         self.display_scale = s

    def centre_view_on(self, world_coords: Coord):
        offset = Coord(self.view_size_tiles.w // 2, self.view_size_tiles.h // 2)
        self.view_world_coord = world_coords.subtract(offset)

    def pixels_to_surface(self, tile_pixels: List[List[int]]) -> pygame.Surface:
        """Convert a 2D list of palette indices into a Pygame Surface."""
        surf = pygame.Surface((self.tile_size_pixels, self.tile_size_pixels))
        pixels = pygame.PixelArray(surf)
        for y, row in enumerate(tile_pixels):
            for x, idx in enumerate(row):
                pixels[(x, y)] = self.palette[idx]
        del pixels  # Unlock the surface
        return surf

    def get_unscaled_surface(self):
        if self._unscaled_surface is None:
            self._unscaled_surface = pygame.Surface(tuple(self.view_size_in_pixels()))
        return self._unscaled_surface

    def get_scaled_surface(self):
        if self._scaled_surface is None:
            self._scaled_surface = pygame.Surface(tuple(self.view_size_in_pixels_scaled()))
        return self._scaled_surface

    def draw_map(self, u5map: U5Map, level_ix: int = 0) -> None:
        """
        Render the map or a subsection of it to a Pygame Surface.
        rect: (tile_x, tile_y, tile_w, tile_h) in tile coordinates.
        """
        u5map_size = Size(u5map.width, u5map.height)
        viewport_surf = self.get_unscaled_surface()

        for y in range(self.view_size_tiles.h):
            for x in range(self.view_size_tiles.w):
                map_coord = Coord(x, y).add(self.view_world_coord)

                # Don't try to pull a tile from outside the source map.
                # If out of bounds, use grass tile.
                if map_coord.is_in_bounds(u5map_size):
                    tid = u5map.get_tile_id(level_ix, map_coord.x, map_coord.y)
                else:
                    tid = TILE_ID_GRASS

                # Don't try to render a non-existant tile id.
                if 0 <= tid < len(u5map.tileset):
                    tile_pixels = u5map.tileset[tid]
                    tile_surf = self.pixels_to_surface(tile_pixels)

                    # draw the tile surface onto the viewport surface.
                    viewport_surf.blit(tile_surf, (x * self.tile_size_pixels, y * self.tile_size_pixels))
                else:
                    print(f"Warning: tile id {tid} out of range, skipping render.")

        return viewport_surf

    def draw_sprite(self, sprite: Sprite) -> None:
        """
        Draw a sprite to the surface.
        If cam_x/cam_y are provided, position is relative to camera (world coords).
        Otherwise, position is treated as screen coords.
        """
        # Determine screen position
        sprite_coord = Coord(sprite.world_x, sprite.world_y)
        screen_coord = sprite_coord.subtract(self.view_world_coord).scale(self.tile_size_pixels)

        # Convert raw pixels to a Surface
        frame_pixels = sprite.get_current_frame_pixels()
        frame_surface = self.pixels_to_surface(frame_pixels)

        # Draw
        viewport_surf = self.get_unscaled_surface()
        viewport_surf.blit(frame_surface, tuple(screen_coord))


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
        view_port = ViewPort(palette=ega_palette)
        self.main_display = MainDisplay(view_port)
        self.screen = pygame.display.set_mode(tuple(self.main_display.size_in_pixels()))
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.player: Sprite = None
        self.sprites: List[Sprite] = []
        self.active_map: Optional[U5Map] = None
        self.active_level = 0

    def register_player(self, player: Sprite) -> None:
        self.player = player
        self.register_sprite(player)

    def register_sprite(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)

    def unregister_sprite(self, sprite: Sprite) -> None:
        self.sprites.remove(sprite)

    def set_active_map(self, u5map: U5Map, map_level: int) -> None:
        self.active_map = u5map
        self.active_level = map_level

    def render(self):

        # Update window title with current location/world of player.
        pygame.display.set_caption(f"{self.active_map.name} [{self.player.world_x},{self.player.world_y}]")

        # Centre the viewport on the player.
        self.main_display.view_port.centre_view_on(Coord(self.player.world_x, self.player.world_y))

        # Render current viewport from raw map data
        self.main_display.view_port.draw_map(
            self.active_map,
            self.active_level
        )

        for sprite in self.sprites:
            self.main_display.view_port.draw_sprite(sprite)

        # Scale for display
        scaled_surface = self.main_display.view_port.get_scaled_surface()
        pygame.transform.scale(
            surface = self.main_display.view_port.get_unscaled_surface(),
            size = scaled_surface.get_size(),
            dest_surface = scaled_surface
        )

        # Blit to screen
        self.screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()

    def update_sprites(self):
        dt_seconds = self.clock.tick(self.fps) / 1000.0  # dt in seconds

        # Update all animated sprites here
        for sprite in self.sprites:
            sprite.update(dt_seconds)