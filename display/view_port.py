# file: display/view_port.py
import pygame

from dark_libraries.dark_math import Coord, Size, Rect
from display.tileset import Tile

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

class ViewPort(ScalableComponent):

    # Injectable Properties
    display_config: DisplayConfig

    def __init__(self):
        pass

    def _after_inject(self):
        super().__init__(
            unscaled_size_in_pixels = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )
        self.view_rect = Rect(Coord(0,0), self.display_config.VIEW_PORT_SIZE)

    def _get_view_centre_in_world_coords(self) -> Coord:
        offset = self.view_rect.size.to_offset() // 2
        view_centre = self.view_rect.minimum_corner + offset
        return view_centre

    def centre_view_on(self, world_coord: Coord) -> None:
        if self._get_view_centre_in_world_coords() != world_coord:
            offset = self.view_rect.size.to_offset() // 2
            new_corner = world_coord - offset
            self.view_rect = Rect(new_corner, self.view_rect.size)

    def to_view_port_coord(self, world_coord: Coord) -> Coord:
        return world_coord - self.view_rect.minimum_corner

    def draw_map(self, tiles: dict[Coord, Tile]) -> None:

        self._clear()

        for coord, tile in tiles.items():
            self.draw_tile(coord, tile)

    def draw_tile(self, world_coord: Coord, tile: Tile):
        screen_coord = self.to_view_port_coord(world_coord).scale(self.display_config.TILE_SIZE)
        tile.blit_to_surface(
            self.get_input_surface(), 
            screen_coord
        )

    '''
    def draw_sprite(self, world_coord: Coord, a_sprite: Sprite) -> None:
        # Get the current animation frame tile.
        ticks = pygame.time.get_ticks()
        frame_tile = a_sprite.get_current_frame_tile(ticks)

        self.draw_tile(world_coord, frame_tile)
    '''

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
