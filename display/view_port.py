# file: display/view_port.py
import pygame
from typing import Optional, Dict

import animation.sprite as sprite
from animation.sprite_registry import SpriteRegistry
from game.interactable import InteractableState
from game.u5map import U5Map

from loaders.tileset import TILE_ID_GRASS, EgaPalette, Tile
from dark_libraries.dark_math import Coord, Size, Rect

class ViewPort:

    # Injectable Properties
    palette: EgaPalette
    interactable_state: InteractableState
    sprite_registry: SpriteRegistry

    world_rect = Rect(Coord(0,0), Size(21,15))
    tile_size_pixels: int = 16
    display_scale: int = 2

    def _after_inject(self):
        # input surface
        self._unscaled_surface: Optional[pygame.Surface] = pygame.Surface(self.view_size_in_pixels().to_tuple())
        # output surface
        self._scaled_surface: Optional[pygame.Surface] = pygame.Surface(self.view_size_in_pixels_scaled().to_tuple())


    def view_size_in_pixels(self) -> Size:
         return self.world_rect.size.scale(self.tile_size_pixels)
    
    def view_size_in_pixels_scaled(self) -> Size:
         return self.view_size_in_pixels().scale(self.display_scale)

    def set_display_scale(self, s: int) -> None:
         self.display_scale = s


    def _get_view_centre(self) -> Coord:
        width, height = self.world_rect.size.to_tuple()
        offset = Coord(width // 2, height // 2)
        view_centre = self.world_rect.minimum_corner.add(offset)

        return view_centre

    def centre_view_on(self, world_coord: Coord) -> None:

        if self._get_view_centre() != world_coord:

            width, height = self.world_rect.size.to_tuple()
            offset = Coord(width // 2, height // 2)
            new_corner = world_coord.subtract(offset)

            self.world_rect = Rect(new_corner, Size(width, height))

    def to_view_port_coord(self, world_coord: Coord) -> Coord:
        return world_coord.subtract(self.world_rect.minimum_corner)

    def get_input_surface(self) -> pygame.Surface:
        return self._unscaled_surface

    def get_output_surface(self) -> pygame.Surface:

        pygame.transform.scale(
            surface      = self._unscaled_surface,
            size         = self.view_size_in_pixels_scaled().to_tuple(),
            dest_surface = self._scaled_surface
        )

        return self._scaled_surface

    def draw_map(self, u5map: U5Map, level_ix: int = 0) -> None:

        for world_coord in self.world_rect:

            # Don't try to pull a tile from outside the source map.
            # If out of bounds, use grass tile.
            if not u5map.is_in_bounds(world_coord):
                tile = u5map.tileset.tiles[TILE_ID_GRASS]
                self.draw_tile(world_coord, tile)
                continue

            tid = u5map.get_tile_id(level_ix, world_coord)

            # if the tile is animated, pull a frame tile from the sprite and draw that instead.
            sprite = self.sprite_registry.get_sprite(tid)
            if sprite:
                self.draw_sprite(world_coord, sprite)
                continue

            interactable = self.interactable_state.get_interactable(tid, world_coord)
            if interactable:
                sprite = interactable.create_sprite()
                self.draw_sprite(world_coord, sprite)
                continue

            # Don't try to render a non-existant tile id.
            if 0 <= tid < len(u5map.tileset.tiles):
                tile: Tile = u5map.tileset.tiles[tid]

                self.draw_tile(world_coord, tile)

            else:
                print(f"Warning: tile id {tid!r} out of range, skipping render.")

    def draw_tile(self, world_coord: Coord, tile: Tile):
        screen_coord = self.to_view_port_coord(world_coord).scale(self.tile_size_pixels)
        tile.blit_to_surface(
            self.get_input_surface(), 
            screen_coord
        )

    def draw_sprite(self, world_coord: Coord, sprite: sprite.Sprite) -> None:

        """
        Draw a sprite to the Viewport
        """
        # Get the current animation frame tile.
        ticks = pygame.time.get_ticks()
        frame_tile = sprite.get_current_frame_tile(ticks)

        self.draw_tile(world_coord, frame_tile)

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

#
# MAIN tests
#
if __name__ == "__main__":

    from loaders.tileset import _ega_palette
    from display.view_port import ViewPort
    from loaders.overworld import load_britannia


    class StubInteractableState:
        def get_interactable(self, tid, world_coord):
            return None
        
    class StubSpriteRegistry:
        def get_sprite(self, tile_id):
            return None

    pygame.init()

    # Manual injection
    view_port = ViewPort()
    view_port.interactable_state = StubInteractableState()
    view_port.sprite_registry = StubSpriteRegistry()
    view_port.palette = _ega_palette

    view_port.world_rect = Rect(Coord(40,40), Size(5,5))
    screen = pygame.display.set_mode(view_port.view_size_in_pixels_scaled().to_tuple())
    
    view_port._after_inject()

    u5map = load_britannia()
    view_port.centre_view_on(Coord(42,42))
    view_port.draw_map(u5map, 0)

    screen.blit(view_port.get_output_surface(),(0,0))
    pygame.display.flip()

    # wait for "any" key to be pressed
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()
