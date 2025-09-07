# file: display/view_port.py
import pygame
from typing import Optional, Dict

from display.engine_protocol import EngineProtocol
import animation.sprite as sprite
from game.u5map import U5Map

from loaders.tileset import TILE_ID_GRASS, EgaPalette, Tile
from dark_libraries.dark_math import Coord, Size, Rect

class ViewPort:

    # Injectable Properties
    engine: EngineProtocol
    palette: EgaPalette


    world_rect = Rect(Coord(0,0), Size(21,15))
#    view_world_coord: Coord = Coord(0, 0)
#    view_size_tiles: Size = Size(21, 15)
    tile_size_pixels: int = 16
    display_scale: int = 2

    def _after_inject(self):
        # input surface
        self._unscaled_surface: Optional[pygame.Surface] = pygame.Surface(self.view_size_in_pixels().to_tuple())
        # output surface
        self._scaled_surface: Optional[pygame.Surface] = pygame.Surface(self.view_size_in_pixels_scaled().to_tuple())

        self._animated_tiles: Dict[int, sprite.Sprite] = dict()

    def view_size_in_pixels(self) -> Size:
         return self.world_rect.size.scale(self.tile_size_pixels)
    
    def view_size_in_pixels_scaled(self) -> Size:
         return self.view_size_in_pixels().scale(self.display_scale)

    def set_display_scale(self, s: int) -> None:
         self.display_scale = s

    def register_animated_tile(self, tile_id: int, sprite_master: sprite.Sprite) -> None:
        self._animated_tiles[tile_id] = sprite_master

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
#        if self._unscaled_surface is None:
#            self._unscaled_surface = pygame.Surface(self.view_size_in_pixels().to_tuple())
        return self._unscaled_surface

    def get_output_surface(self) -> pygame.Surface:
#        if self._scaled_surface is None:
#            self._scaled_surface = pygame.Surface(self.view_size_in_pixels_scaled().to_tuple())
        return self._scaled_surface

    def draw_map(self, u5map: U5Map, level_ix: int = 0) -> None:
        viewport_surface = self.get_input_surface()

        for world_x, world_y in self.world_rect:
            world_coord = Coord(world_x, world_y)

            # Don't try to pull a tile from outside the source map.
            # If out of bounds, use grass tile.
            if u5map.is_in_bounds(world_coord):
                tid = u5map.get_tile_id(level_ix, world_coord)
            else:
                tid = TILE_ID_GRASS

            # if the tile is animated, register a sprite
            if tid in self._animated_tiles.keys():
                sprite_master = self._animated_tiles[tid]
                sprite_copy = sprite_master.spawn_from_master(world_coord)

                self.engine.register_sprite(sprite_copy)

            interactable = self.engine.world_state.get_interactable(tid, world_coord)
            if interactable:
                self.engine.register_sprite(interactable.create_sprite())

            # Don't try to render a non-existant tile id.
            if 0 <= tid < len(u5map.tileset.tiles):
                tile: Tile = u5map.tileset.tiles[tid]
                screen_coord = self.to_view_port_coord(world_coord).scale(self.tile_size_pixels)

                tile.blit_to_surface(
                    viewport_surface, 
                    screen_coord
                )

            else:
                print(f"Warning: tile id {tid!r} out of range, skipping render.")

    def draw_sprite(self, sprite: sprite.Sprite) -> None:

        """
        Draw a sprite to the Viewport
        """
        # Determine screen position
        screen_coord = sprite.world_coord.subtract(self.world_rect.minimum_corner).scale(self.tile_size_pixels)

        # Get the current animation frame tile.
        ticks = pygame.time.get_ticks()
        frame_tile = sprite.get_current_frame_tile(ticks)

        # Draw
        frame_tile.blit_to_surface(
            target_surface = self.get_input_surface(),
            pixel_offset = screen_coord
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

#
# MAIN tests
#
if __name__ == "__main__":

    from loaders.tileset import _ega_palette
    from display.view_port import ViewPort
    from loaders.overworld import load_britannia


    class StubWorldState:
        def get_interactable(self, tid, world_coord):
            return None
        
    class StubEngine:
        def __init__(self):
            self.world_state = StubWorldState()

        def register_sprite(self, sprite_copy):
            pass

    pygame.init()

    # Manual injection
    view_port = ViewPort()
    view_port.engine = StubEngine()
    view_port.palette = _ega_palette
    view_port.world_rect = Rect(Coord(40,40), Size(5,5))

    screen = pygame.display.set_mode(view_port.world_rect.size.to_tuple())
    view_port._after_inject()

    u5map = load_britannia()
    view_port.centre_view_on(Coord(42,42))
    view_port.draw_map(u5map, 0)
    