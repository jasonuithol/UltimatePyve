# file: display/view_port.py
import pygame
from typing import Iterator, Optional

from dark_libraries import Coord, Size, Rect, Vector2

import animation.sprite as sprite
from animation import SpriteRegistry
from dark_libraries.custom_decorators import auto_init, immutable
from game.terrain.terrain import Terrain
from game.terrain.terrain_registry import TerrainRegistry
from maps import U5Map
from game.interactable import InteractableFactoryRegistry

from tileset import TILE_ID_GRASS, EgaPalette, Tile, TileSet

WINDOWED_VECTORS = [
    Vector2( 0,  1), # bottom
    Vector2( 0, -1), # top
    Vector2( 1,  0), # right
    Vector2(-1,  0), # left
]

NEIGHBOUR_VECTORS = WINDOWED_VECTORS + [
    Vector2( 1,  1), # bottom-right
    Vector2( 1, -1), # top-right
    Vector2(-1,  1), # bottom-left
    Vector2(-1, -1)  # bottom-right
]

@immutable
@auto_init
class QueriedTile:
    tile: Tile
    terrain: Terrain
    sprite: sprite.Sprite | None

class ViewPort:

    # Injectable Properties
    tileset: TileSet
    palette: EgaPalette
    interactable_factory_registry: InteractableFactoryRegistry
    sprite_registry: SpriteRegistry
    terrain_registry: TerrainRegistry

    # NOTE: Initial Coord will be overwritten during init. We need the Rect's size for size based calcs before init is done.
    view_rect = Rect(Coord(0,0), Size(21,15))

    tile_size_pixels: int = 16
    display_scale: int = 2

    def _after_inject(self):
        # input surface
        self._unscaled_surface: pygame.Surface = pygame.Surface(self.view_size_in_pixels().to_tuple())
        # output surface
        self._scaled_surface: pygame.Surface = pygame.Surface(self.view_size_in_pixels_scaled().to_tuple())

        self.black_mapped_rgb = self._unscaled_surface.map_rgb((0,0,0))
        self.black_tile = Tile(0)
        self.black_tile.load_from_bytes(bytes(128))

    def init(self):
        self.queried_tile_grass = QueriedTile(
            tile    = self.tileset.tiles[TILE_ID_GRASS],
            terrain = self.terrain_registry.get_terrain(TILE_ID_GRASS),
            sprite  = None
        )

        self.queried_tile_black = QueriedTile(
            tile    = self.black_tile,
            terrain = None,
            sprite  = None
        )

    def view_size_in_pixels(self) -> Size:
         return self.view_rect.size.scale(self.tile_size_pixels)
    
    def view_size_in_pixels_scaled(self) -> Size:
         return self.view_size_in_pixels().scale(self.display_scale)

    def set_display_scale(self, s: int) -> None:
         self.display_scale = s

    def _get_view_centre(self) -> Coord:
        width, height = self.view_rect.size.to_tuple()
        offset = Coord(width // 2, height // 2)
        view_centre = self.view_rect.minimum_corner.add(offset)

        return view_centre

    def centre_view_on(self, world_coord: Coord) -> None:

        if self._get_view_centre() != world_coord:

            width, height = self.view_rect.size.to_tuple()
            offset = Coord(width // 2, height // 2)
            new_corner = world_coord.subtract(offset)

            self.view_rect = Rect(new_corner, Size(width, height))

    def to_view_port_coord(self, world_coord: Coord) -> Coord:
        return world_coord.subtract(self.view_rect.minimum_corner)

    def get_input_surface(self) -> pygame.Surface:
        return self._unscaled_surface

    def get_output_surface(self) -> pygame.Surface:

        pygame.transform.scale(
            surface      = self._unscaled_surface,
            size         = self.view_size_in_pixels_scaled().to_tuple(),
            dest_surface = self._scaled_surface
        )

        return self._scaled_surface


    def query_tile_grid(self, u5map: U5Map, level_ix: int = 0) -> Iterator[tuple[Coord, QueriedTile]]:

        result: dict[Coord, int] = {} 
        for world_coord in self.view_rect:

            # Don't try to pull a tile from outside the source map.
            # If out of bounds, use grass tile.
            if not u5map.is_in_bounds(world_coord):
                yield world_coord, self.queried_tile_grass
                continue

            # Allow interactables to change what state an object is e.g. allow doors to open/close/unlock
            # or chests to have loot stacks on them (i.e. be open)
            interactable = self.interactable_factory_registry.get_interactable(world_coord)
            if interactable:
                # Allow get_current_tile_id to return None to signify that the container/interactable is hidden/invisible.
                tile_id: int = interactable.get_current_tile_id()
                '''
                sprite = interactable.create_sprite()
                self.draw_sprite(world_coord, sprite)
                continue
                '''
            else:
                # There is no interactable, but we'll pretend it's just an invisible one.
                tile_id: int = None

            if tile_id is None:
                tile_id = u5map.get_tile_id(level_ix, world_coord)

            # Don't try to render a non-existant tile id.
            assert 0 <= tile_id < len(self.tileset.tiles), f"tile id {tile_id!r} out of range."

            yield world_coord, QueriedTile(
                tile = self.tileset.tiles[tile_id],
                terrain = self.terrain_registry.get_terrain(tile_id),
                # if the tile_id is animated, pull a frame tile from the sprite and draw that instead.
                sprite = self.sprite_registry.get_sprite(tile_id)
            )

        return result

    def calculate_fov_visibility(self, queried_tile_grid: Iterator[tuple[Coord, QueriedTile]]) -> Iterator[tuple[Coord, QueriedTile]]:

        view_centre_coord = self._get_view_centre()
        windowed_coords = [view_centre_coord.add(windowed_vector) for windowed_vector in WINDOWED_VECTORS]

        queried_tile_grid_dict = dict(queried_tile_grid)

        queued: list[Coord] = [view_centre_coord]
        visited: list[Coord] = queued + []

        while len(queued):
            world_coord = queued.pop()
            queried_tile = queried_tile_grid_dict[world_coord]

            yield world_coord, queried_tile

            if world_coord == view_centre_coord or not queried_tile.terrain.blocks_light or (world_coord in windowed_coords and queried_tile.terrain.windowed):
                for neighbour_vector in NEIGHBOUR_VECTORS:
                    neighbour_coord = world_coord.add(neighbour_vector)
                    if self.view_rect.is_in_bounds(neighbour_coord) and not neighbour_coord in visited:
                        queued.append(neighbour_coord)
                        visited.append(neighbour_coord)

    def draw_map(self, u5map: U5Map, level_ix: int = 0) -> None:

        self.get_input_surface().fill(self.black_mapped_rgb)

        queried_tile_grid = self.query_tile_grid(u5map, level_ix)
        visible_grid = self.calculate_fov_visibility(queried_tile_grid)

        for world_coord, queried_tile in visible_grid:
            if queried_tile.sprite:
                self.draw_sprite(world_coord, queried_tile.sprite)
            else:
                self.draw_tile(world_coord, queried_tile.tile)

    def draw_tile(self, world_coord: Coord, tile: Tile):
        screen_coord = self.to_view_port_coord(world_coord).scale(self.tile_size_pixels)
        tile.blit_to_surface(
            self.get_input_surface(), 
            screen_coord
        )

    def draw_sprite(self, world_coord: Coord, a_sprite: sprite.Sprite) -> None:

        """
        Draw a sprite to the Viewport
        """
        # Get the current animation frame tile.
        ticks = pygame.time.get_ticks()
        frame_tile = a_sprite.get_current_frame_tile(ticks)

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

    from tileset.tileset import _ega_palette
    from maps.overworld import load_britannia

    class StubInteractableFactoryRegistry:
        def get_interactable(self, world_coord):
            return None
        
    class StubSpriteRegistry:
        def get_sprite(self, tile_id):
            return None

    pygame.init()

    # Manual injection
    view_port = ViewPort()
    view_port.interactable_factory_registry = StubInteractableFactoryRegistry()
    view_port.sprite_registry = StubSpriteRegistry()
    view_port.palette = _ega_palette

    view_port.view_rect = Rect(Coord(40,40), Size(5,5))
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
