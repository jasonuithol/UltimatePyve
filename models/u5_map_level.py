import colorsys
import threading
import pygame
from dark_libraries.dark_math import Coord, Size
from dark_libraries.registry import Registry
from models.tile import TILE_ID_GRASS, Tile

class U5MapLevel:
    def __init__(self, data: dict[Coord[int], int], size: Size[int]):

        self._data = data
        self._size = size

    def get_tile_id(self, coord: Coord[int]):
        # Allow out-of-bounds queries.
        return self._data.get(coord, None)
    
    def get_size(self):
        return self._size

    def coords(self):
        for y in range(self._size.h):
            for x in range(self._size.w):
                yield Coord[int](x,y)

    def __iter__(self):
        return self._data.items().__iter__()

    def render_to_surface(self, tiles: Registry[int, Tile]) -> pygame.Surface:

        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"

        if tiles:
            scale = list(tiles.values())[0]._get_size()
        else:
            scale = Size[int](1,1)

        surf = pygame.Surface(self._size.scale(scale).to_tuple())

        for map_coord, tile_id in self:

            if tiles:
                tile: Tile = tiles.get(tile_id)
                pixel_coord = map_coord.scale(scale)
                tile.blit_to_surface(surf, pixel_coord)
            else:
                if tile_id == TILE_ID_GRASS:
                    surf.set_at(map_coord.to_tuple(), (0,0,0))
                else:
                    # make similar tile_ids have very different hues.
                    hashed = (tile_id * 197 + 101) & 0xFF

                    hue = ((hashed / 255) + 0.00) % 1 # Normalize to 0–1.  Change the rotation value to slide the hue mapping along the hue circle.
                    r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.6)  # tone down the saturation and brightness
                    color = (int(r * 255), int(g * 255), int(b * 255))
                    surf.set_at(map_coord.to_tuple(), color)

        return surf

    def render_to_disk(self, name: str):

        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"

        from data.global_registry import GlobalRegistry
        from data.loaders.tileset_loader import TileLoader
        from view.display_config import DisplayConfig

        global_registry = GlobalRegistry()

        tile_loader = TileLoader()
        tile_loader.global_registry = global_registry
        tile_loader.display_config = DisplayConfig()
        tile_loader.load_tiles()

        #
        # TODO: use render to surface
        #
        surf = pygame.Surface(self._size.scale(tile_loader.display_config.TILE_SIZE).to_tuple())

        for x in range(self._size.x):
            for y in range(self._size.y):

                map_coord = Coord[int](x, y)
                tile_id = self.get_tile_id(map_coord)
                tile: Tile = tile_loader.global_registry.tiles.get(tile_id)

                pixel_coord = map_coord.scale(tile_loader.display_config.TILE_SIZE)
                tile.blit_to_surface(surf, pixel_coord)
        pygame.image.save(
            surf,
            f"log/{name}.png"
        )
        pygame.quit()
