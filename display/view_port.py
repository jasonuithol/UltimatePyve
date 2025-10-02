# file: display/view_port.py
import pygame

from dark_libraries.dark_math import Coord, Size, Rect

from animation.sprite import Sprite
from animation.sprite_registry import SpriteRegistry

from game.player_state import PlayerState
from game.terrain.terrain_registry import TerrainRegistry
from game.interactable import InteractableFactoryRegistry
from game.world_clock import WorldClock

from maps.u5map import U5Map

from .tileset import Tile, TileRegistry
from .display_config import DisplayConfig
from .scalable_component import ScalableComponent
from .field_of_view import FieldOfViewCalculator
from .lighting import LightMapRegistry
from .queried_tiles import QueriedTileGenerator, QueriedTileResult

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
    player_state: PlayerState

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
        offset = self.view_rect.size.to_offset() // 2
        view_centre = self.view_rect.minimum_corner + offset
        return view_centre

    def centre_view_on(self, world_coord: Coord) -> None:
        if self._get_view_centre() != world_coord:
            offset = self.view_rect.size.to_offset() // 2
            new_corner = world_coord - offset
            self.view_rect = Rect(new_corner, self.view_rect.size)

    def to_view_port_coord(self, world_coord: Coord) -> Coord:
        return world_coord - self.view_rect.minimum_corner

    def calculate_lighting(self, queried_tile_grid: QueriedTileResult, location_index: int, level_index: int) -> QueriedTileResult:
        
        current_radius = self.world_clock.get_current_light_radius()

        # in case the player has lit a torch or something
        if not self.player_state.light_radius is None:
            current_radius = max(current_radius, self.player_state.light_radius)
            
        viewable_radius = max(1, min(current_radius, self.light_map_registry.get_maximum_radius()))

        baked_player_light_map = self.light_map_registry.get_light_map(viewable_radius).translate(self._get_view_centre()).intersect(queried_tile_grid.keys())
        baked_level_light_maps = self.light_map_registry.get_baked_light_maps(location_index, level_index)

        lit_world_coords: set[Coord] = set(baked_player_light_map.coords.keys())
        if not baked_level_light_maps is None:
            for light_emitter_coord, level_light_map in baked_level_light_maps.items():
                if light_emitter_coord in queried_tile_grid.keys():
                    lit_world_coords.update(level_light_map.coords.keys())

        result = QueriedTileResult()
        for world_coord, queried_tile in queried_tile_grid.items():
            if world_coord in lit_world_coords:
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

    def draw_sprite(self, world_coord: Coord, a_sprite: Sprite) -> None:
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
