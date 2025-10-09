from dark_libraries.dark_math import Coord, Size

class U5MapLevel:
    def __init__(self, data: dict[Coord, int], size: Size):

        self._data = data
        self._size = size

    def get_tile_id(self, coord: Coord):
        # Allow out-of-bounds queries.
        return self._data.get(coord, None)
    
    def get_size(self):
        return self._size

    def coords(self):
        for y in range(self._size.h):
            for x in range(self._size.w):
                yield Coord(x,y)

    def __iter__(self):
        return self._data.items().__iter__()

    def render_to_disk(self, name: str):

        import pygame
        from models.tile import Tile
        from data.global_registry import GlobalRegistry
        from data.loaders.tileset_loader import TileLoader
        from view.display_config import DisplayConfig

        pygame.init()

        global_registry = GlobalRegistry()
        global_registry._after_inject()

        tile_loader = TileLoader()
        tile_loader.global_registry = global_registry
        tile_loader.display_config = DisplayConfig()
        tile_loader.load_tiles()

        surf = pygame.Surface(self._size.scale(tile_loader.display_config.TILE_SIZE).to_tuple())
        for x in range(self._size.x):
            for y in range(self._size.y):

                map_coord = Coord(x, y)
                tile_id = self.get_tile_id(map_coord)
                tile: Tile = tile_loader.global_registry.tiles.get(tile_id)

                pixel_coord = map_coord.scale(tile_loader.display_config.TILE_SIZE)
                tile.blit_to_surface(surf, pixel_coord)
        pygame.image.save(
            surf,
            f"log/{name}.png"
        )
        pygame.quit()
