# file: display/view_port.py
import pygame

from copy import copy
from dark_libraries.dark_math import Coord, Size, Rect

import animation.sprite as sprite
from animation.sprite_registry import SpriteRegistry

from display.field_of_view import FieldOfViewCalculator
from display.lighting import LightMapRegistry
from display.queried_tiles import QueriedTile, QueriedTileGenerator, QueriedTileResult
from game.terrain.terrain_registry import TerrainRegistry
from game.interactable import InteractableFactoryRegistry

from game.world_clock import WorldClock
from maps.u5map import U5Map

from .tileset import Tile, TileRegistry
from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

class ViewPort(ScalableComponent):

    # Injectable Properties
    display_config: DisplayConfig
    tileset: TileRegistry
    interactable_factory_registry: InteractableFactoryRegistry
    sprite_registry: SpriteRegistry
    terrain_registry: TerrainRegistry
    light_map_registry: LightMapRegistry
    world_clock: WorldClock
    queried_tile_generator: QueriedTileGenerator
    fov_calculator: FieldOfViewCalculator

    def __init__(self):
        pass

    def _after_inject(self):
        super().__init__(
            unscaled_size_in_pixels = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )
        self.view_rect = Rect(Coord(0,0), self.display_config.VIEW_PORT_SIZE)

    # returns WORLD COORDS
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

    def calculate_lighting(self, queried_tile_grid: QueriedTileResult, location_index: int, level_index: int) -> QueriedTileResult:

        current_radius = self.world_clock.get_current_light_radius()
        viewable_radius = max(1, min(current_radius, self.light_map_registry.get_maximum_radius()))

        player_light_map = self.light_map_registry.get_light_map(viewable_radius)
        level_light_map_copy = self.light_map_registry.get_baked_light_map(location_index, level_index).copy()
        player_coord = self._get_view_centre()

        player_light_map.bake_level_light_map(level_light_map_copy, player_coord, None)

        result = QueriedTileResult()
        for world_coord, queried_tile in queried_tile_grid.items():
            if world_coord in level_light_map_copy:
                result[world_coord] = queried_tile
        return result

    def draw_map(self, u5map: U5Map, level_ix: int = 0) -> None:

        self._clear()

        queried_tile_grid = self.queried_tile_generator.query_tile_grid(u5map, level_ix, self.view_rect)
        visible_grid = self.fov_calculator.calculate_fov_visibility(queried_tile_grid, self._get_view_centre(), self.view_rect)
        lit_grid = self.calculate_lighting(visible_grid, u5map.location_metadata.location_index, level_ix)

        for world_coord, queried_tile in lit_grid.items():
            if queried_tile.sprite:
                self.draw_sprite(world_coord, queried_tile.sprite)
            else:
                self.draw_tile(world_coord, queried_tile.tile)

    def draw_tile(self, world_coord: Coord, tile: Tile):
        screen_coord = self.to_view_port_coord(world_coord).scale(self.display_config.TILE_SIZE)
        tile.blit_to_surface(
            self.get_input_surface(), 
            screen_coord
        )

    def draw_sprite(self, world_coord: Coord, a_sprite: sprite.Sprite) -> None:
        # Get the current animation frame tile.
        ticks = pygame.time.get_ticks()
        frame_tile = a_sprite.get_current_frame_tile(ticks)

        self.draw_tile(world_coord, frame_tile)

#
# MAIN tests
#
if __name__ == "__main__":

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

    view_port.view_rect = Rect(Coord(40,40), Size(5,5))
    screen = pygame.display.set_mode(view_port.scaled_size().to_tuple())
    
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
