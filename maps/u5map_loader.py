# file: maps/location.py

from copy import copy
from pathlib import Path
from dark_libraries import Size

from .location_metadata_builder import LocationMetadataBuilder
from .u5map import U5Map
from .u5map_registry import U5MapRegistry
from .overworld import Britannia
from .underworld import UnderWorld

class U5MapLoader:

    # Injectable
    builder: LocationMetadataBuilder
    registry: U5MapRegistry
    brittania: Britannia
    underworld: UnderWorld

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
        filename = U5MapLoader.FILES[meta.files_index]

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
            size_in_tiles       = Size(LOCATION_WIDTH,LOCATION_HEIGHT),
            levels              = dict(enumerate(levels)),
            chunk_dim           = CHUNK_DIM,
            grid_dim            = GRID_DIM,
            location_metadata   = meta
        )

    def build_world_map(self):

        levels: dict[int, bytearray] = {}
        levels[0] = self.brittania.levels[0]
        levels[255] = self.underworld.levels[0]

        world = U5Map(
            size_in_tiles = self.brittania.size_in_tiles,
            levels = levels,
            chunk_dim = self.brittania.chunk_dim,
            grid_dim = self.brittania.grid_dim,
            location_metadata = self.builder.build_overworld_metadata()
        )

        return world

    def register_maps(self):
        for trigger_index in range(self.get_number_locations()):
            u5map: U5Map = self.load_location_map(trigger_index)
            self.registry.register_map(u5map)

        world = self.build_world_map()
        self.registry.register_map(world)

if __name__ == "__main__":

    from .data import DataOVL
    from .overworld import load_britannia
    from .underworld import load_underworld

    dataOvl = DataOVL.load()

    # Injectable
    builder = LocationMetadataBuilder()
    builder.dataOvl = dataOvl

    registry = U5MapRegistry()
    registry._after_inject()

    loader = U5MapLoader()
    loader.builder = builder
    loader.registry = registry
    loader.brittania = load_britannia()
    loader.underworld = load_underworld()
    loader._after_inject()

    loader.register_maps()

    for u5map in registry.u5maps.values():
        for level_index in u5map.levels.keys():
            try:
                surf = u5map.render_to_disk(level_index)
            except Exception as e:
                print(f"Error rendering {u5map.location_metadata.name!r} level {level_index!r}: {e}")
                raise e
    print("All maps dumped.")

