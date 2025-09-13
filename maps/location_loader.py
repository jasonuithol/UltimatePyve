# file: maps/location.py

from pathlib import Path
from dark_libraries import Size

from .location_metadata_builder import LocationMetadataBuilder
from .u5map import U5Map

class LocationLoader:

    # Injectable
    builder: LocationMetadataBuilder

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
            levels              = levels,
            chunk_dim           = CHUNK_DIM,
            grid_dim            = GRID_DIM,
            location_metadata   = meta
        )




if __name__ == "__main__":

    from dark_libraries.service_provider import ServiceProvider
    import maps.service_composition

    provider = ServiceProvider()
    maps.service_composition.compose(provider)

    loader: LocationLoader = provider.get(LocationLoader)
    trigger_index = 0
    for trigger_index in range(loader.get_number_locations()):
        u5map: U5Map = loader.load_location_map(trigger_index)
        for level in range(len(u5map.levels)):
            try:
                surf = u5map.render_to_disk(level)
            except Exception as e:
                print(f"Error rendering {u5map.name!r} level {level!r}: {e}")
                raise e
    print("All maps dumped.")

