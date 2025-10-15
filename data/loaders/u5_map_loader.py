from pathlib import Path
from dark_libraries.dark_math import Size
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.u5_map import U5Map
from models.u5_map_level import U5MapLevel
from models.data_ovl import DataOVL

from .location_metadata_builder import LocationMetadataBuilder

class U5MapLoader(LoggerMixin):

    # Injectable
    builder: LocationMetadataBuilder
    global_registry: GlobalRegistry
    data_ovl: DataOVL

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

    @classmethod
    def convert_tilearray_to_map_level(cls, tiledata: bytearray, map_size: Size) -> U5MapLevel:
        tiles_dict = {
            coord : tiledata[(map_size.w * coord.y) + coord.x]
            for coord in map_size
        }
        return U5MapLevel(
            data = tiles_dict,
            size = map_size
        )
    
    def load_location_map(self, trigger_index: int) -> U5Map:

        LOCATION_WIDTH  = 32
        LOCATION_HEIGHT = 32

        meta = self.metadata[trigger_index]
        filename = U5MapLoader.FILES[meta.files_index]

        path = Path("u5") / filename
        if not path.exists():
            raise FileNotFoundError(f"Map file not found: {filename!r}")

        map_size = Size(LOCATION_WIDTH, LOCATION_HEIGHT)
        map_byte_length = LOCATION_WIDTH * LOCATION_HEIGHT
        offset = meta.map_index_offset * map_byte_length

        levels = list[U5MapLevel]()
        with open(path, "rb") as f:
            f.seek(offset)
            for _ in range(meta.num_levels):
                tile_ids = bytearray(f.read(map_byte_length))
                map_level = __class__.convert_tilearray_to_map_level(tile_ids, map_size)
                levels.append(map_level)

        return U5Map(
            levels              = dict(enumerate(levels)),
            location_metadata   = meta
        )

    def load_britannia(self) -> U5MapLevel:

        # === CONSTANTS ===
        GRID_DIM    = 16
        CHUNK_DIM   = 16
        MAP_DIM     = GRID_DIM * CHUNK_DIM
        VOID_MARKER = 0xFF

        ovl = self.data_ovl
        chunk_map = list(ovl.britannia_chunking_info)
        chunks_data = Path(r".\u5\BRIT.DAT").read_bytes()
        chunk_list = [chunks_data[i*256:(i+1)*256] for i in range(len(chunks_data)//256)]
        
        # The overworld has a lot of empty ocean, so Origin decided to compress it.
        # This means they saved 10's of bytes, but we now have to uncompress it.
        ocean_chunk = bytes([0x01] * (CHUNK_DIM * CHUNK_DIM))
        tiles = bytearray(MAP_DIM * MAP_DIM)
        for gy in range(GRID_DIM):
            for gx in range(GRID_DIM):
                cid = chunk_map[gy*GRID_DIM + gx]
                chunk = ocean_chunk if cid == VOID_MARKER or cid >= len(chunk_list) else chunk_list[cid]
                for cy in range(CHUNK_DIM):
                    dst = (gy*CHUNK_DIM + cy) * MAP_DIM + gx*CHUNK_DIM
                    src = cy * CHUNK_DIM
                    tiles[dst:dst+CHUNK_DIM] = chunk[src:src+CHUNK_DIM]
        
        # Convert to U5MapLevel compatible format.                    
        map_size = Size(MAP_DIM, MAP_DIM)
        return __class__.convert_tilearray_to_map_level(tiles, map_size)

    @classmethod
    def load_underworld(cls) -> U5MapLevel:

        # === CONSTANTS ===
        GRID_DIM   = 16       # 16×16 chunks
        CHUNK_DIM  = 16       # 16×16 tiles per chunk
        MAP_DIM    = GRID_DIM * CHUNK_DIM  # 256×256 tiles

        raw = Path(r".\u5\UNDER.DAT").read_bytes()
        # UNDER.DAT is exactly 256 chunks × 256 bytes each
        chunks = [raw[i*256:(i+1)*256] for i in range(len(raw)//256)]
        tiles = bytearray(MAP_DIM * MAP_DIM)
        for gy in range(GRID_DIM):
            for gx in range(GRID_DIM):
                chunk = chunks[gy*GRID_DIM + gx]
                for cy in range(CHUNK_DIM):
                    dst = (gy*CHUNK_DIM + cy) * MAP_DIM + gx*CHUNK_DIM
                    src = cy * CHUNK_DIM
                    tiles[dst:dst+CHUNK_DIM] = chunk[src:src+CHUNK_DIM]

                # Convert to U5MapLevel compatible format.                    
        map_size = Size(MAP_DIM, MAP_DIM)
        return __class__.convert_tilearray_to_map_level(tiles, map_size)
    
    def build_world_map(self):

        levels: dict[int, U5MapLevel] = {}
        levels[0]   = self.load_britannia()
        levels[255] = __class__.load_underworld()

        world = U5Map(
            levels = levels,
            location_metadata = self.builder.build_overworld_metadata()
        )

        return world

    def register_maps(self):
        for trigger_index in range(self.get_number_locations()):
            u5map: U5Map = self.load_location_map(trigger_index)
            self.global_registry.maps.register(u5map.location_index, u5map)
            self.log(f"DEBUG: Loaded map {u5map.name} containing {len(u5map.get_level_indexes())} levels.")

        world = self.build_world_map()
        self.log(f"DEBUG: Loaded map {world.name} containing {len(world.get_level_indexes())} levels.")
        self.global_registry.maps.register(world.location_index, world)
        self.log(f"Loaded {len(self.global_registry.maps)} maps.")

if __name__ == "__main__":

    from models.data_ovl import DataOVL

    dataOvl = DataOVL.load()

    # Injectable
    builder = LocationMetadataBuilder()
    builder.dataOvl = dataOvl

    registry = GlobalRegistry()

    loader = U5MapLoader()
    loader.builder = builder
    loader.global_registry = registry
    loader.data_ovl = dataOvl
    loader._after_inject()

    loader.register_maps()

    for u5map in registry.maps.values():
        surf = u5map.render_to_disk()
    print("All maps dumped.")

