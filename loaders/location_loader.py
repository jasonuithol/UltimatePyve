# file: loaders/location.py

from pathlib import Path
from dark_libraries import Coord, Size

from .location_metadata_builder import LocationMetadataBuilder
from .tileset import TileSet
from .u5map import U5Map

class LocationLoader:

    # Injectable
    builder: LocationMetadataBuilder
    tileset: TileSet

    FILES = [
        "TOWNE.DAT",
        "DWELLING.DAT",
        "CASTLE.DAT",
        "KEEP.DAT"
    ]

    def _after_inject(self):

        self.metadata = self.builder.build_metadata()

    def get_number_locations(self) -> int:
        return len(self.metadata)

    def load_location_map(self, trigger_index: int) -> U5Map:

        LOCATION_WIDTH = 32
        LOCATION_HEIGHT = 32
        CHUNK_DIM = 16
        GRID_DIM = LOCATION_WIDTH // CHUNK_DIM

        meta = self.metadata[trigger_index]
        filename = LocationLoader.FILES[meta.files_index]

        path = Path("u5") / filename
        if not path.exists():
            raise FileNotFoundError(f"Map file not found: {filename!r}")

        map_size = LOCATION_WIDTH * LOCATION_HEIGHT
        offset = meta.map_index_offset * map_size

        levels = []
        with open(path, "rb") as f:
            f.seek(offset)
            for _ in range(meta.num_levels):
                tile_ids = bytearray(f.read(map_size))
                levels.append(tile_ids)

        return U5Map(
            name                = meta.name,
            size_in_tiles       = Size(LOCATION_WIDTH,LOCATION_HEIGHT),
            tileset             = self.tileset,  # raw pixel data
            levels              = levels,
            chunk_dim           = CHUNK_DIM,
            grid_dim            = GRID_DIM,
            location_metadata   = meta
        )

    def render_location_map_to_disk(self, u5map: U5Map, level: int) -> U5Map:
        import pygame
        from loaders.tileset import Tile
        pygame.init()
        surf = pygame.Surface(u5map.size_in_tiles.scale(self.tileset.tile_size).to_tuple())
        for x in range(u5map.size_in_tiles.x):
            for y in range(u5map.size_in_tiles.y):

                map_coord = Coord(x, y)
                tile_id = u5map.get_tile_id(level, map_coord)
                tile: Tile = self.tileset.tiles[tile_id]

                pixel_coord = map_coord.scale(self.tileset.tile_size)
                tile.blit_to_surface(surf, pixel_coord)
        pygame.image.save(
            surf,
            f"{u5map.name}_{level}.png"
        )
        pygame.quit()

        return surf


if __name__ == "__main__":

    from dark_libraries.service_provider import ServiceProvider
    import loaders.service_composition

    provider = ServiceProvider()
    loaders.service_composition.compose(provider)

    loader: LocationLoader = provider.get(LocationLoader)
    trigger_index = 0
    for trigger_index in range(loader.get_number_locations()):
        u5map = loader.load_location_map(trigger_index)
        for level in range(len(u5map.levels)):
            try:
                surf = loader.render_location_map_to_disk(u5map, level)
            except Exception as e:
                print(f"Error rendering {u5map.name!r} level {level!r}: {e}")
                raise e
    print("All maps dumped.")

