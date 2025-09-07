# file: loaders/location.py

#
# INNER LOCATIONS (i.e. TOWNES KEEPS CASTLES DWELLINGS)   TODO: DUNGEONS
#

from typing import List
from pathlib import Path
from game.u5map import U5Map, LocationMetadata
from loaders.tileset import TileSet
from loaders.data import DataOVL
from dark_libraries.dark_math import Coord, Size

class LocationMetadataBuilder:

    # Injectable
    dataOvl: DataOVL

    '''
    LOCATION_METADATA
    List of Tuple(location_name_index, files_index, num_levels)
    NOTE: 
        Order is important: group_index, map_index_offset, trigger_index will be calculated 
        off of order of appearance (first two within unique values of files_index.)
        
        This is the same order of appearance that the maps make in the .DAT files/entry trigger co-ordinate lists.
    '''
    LOCATION_METADATA = [
        # === TOWNE.DAT ===
        (0, 0, 2),   # 0  MOONGLOW                  [ 0]            
        (1, 0, 2),   # 1  BRITAIN                   [ 1]
        (2, 0, 2),   # 2  JHELOM                    [ 2]
        (3, 0, 2),   # 3  YEW                       [ 3]
        (4, 0, 2),   # 4  MINOC                     [ 4]
        (5, 0, 2),   # 5  TRINSIC                   [ 5]
        (6, 0, 2),   # 6  SKARA BRAE                [ 6]
        (7, 0, 2),   # 7  NEW MAGINCIA              [ 7]

        # === DWELLING.DAT ===
        (8, 1, 3),  # 8  FOGSBANE                   [ 8]
        (9, 1, 3),  # 9  STORMCROW
        (10, 1, 3),  # 10 GREYHAVEN
        (11, 1, 3),  # 11 WAVEGUIDE
        (12, 1, 1),  # 12 IOLO'S HUT                [12]
        (29, 1, 1),  # 29 SPEKTRAN
        (30, 1, 1),  # 30 SIN'VRAAL'S HUT           [14]
        (31, 1, 1),   # 31 GRENDEL'S HUT            [15]
            
        # === CASTLE.DAT ===
        (27, 2, 5),  # 27 LORD BRITISH'S CASTLE     [16]
        (28, 2, 5),  # 28 BLACKTHORN'S CASTLE       [17]
        (13, 2, 1),  # 13 WEST BRITANNY             [18]  
        (14, 2, 1),  # 14 NORTH BRITANNY            [19]
        (15, 2, 1),  # 15 EAST BRITANNY             [20]
        (16, 2, 1),  # 16 PAWS                      [21]
        (17, 2, 1),  # 17 COVE                      [22]
        (18, 2, 1),  # 18 BUCCANEER'S DEN

        # === KEEP.DAT ===
        (19, 3, 2),  # 19 ARARAT                    [24]
        (20, 3, 2),  # 20 BORDERMARCH
        (21, 3, 1),  # 21 FARTHING
        (22, 3, 1),  # 22 WINDEMERE
        (23, 3, 1),  # 23 STONEGATE
        (24, 3, 3),  # 24 THE LYCAEUM
        (25, 3, 3),  # 25 EMPATH ABBEY              [30]
        (26, 3, 3),  # 26 SERPENT'S HOLD

        # TODO: DUNGEONS
    ]

    def build_location_names(self) -> list[str]:
        location_names = [p.decode('ascii') for p in self.dataOvl.city_names_caps.split(b'\x00') if p]

        # Append missing names (these are not in city_names_caps)
        location_names += [
            "LORD BRITISH'S CASTLE",
            "BLACKTHORN'S CASTLE",
            "SPEKTRAN",
            "SIN'VRAAL'S HUT",
            "GRENDEL'S HUT"
        ]        
        return location_names

    def build_default_level_lists(self) -> List[bytes]:
        return  [
            self.dataOvl.map_index_towne,
            self.dataOvl.map_index_dwelling,
            self.dataOvl.map_index_castle,
            self.dataOvl.map_index_keep
        ]

    def build_metadata(self) -> List[LocationMetadata]:
        #
        # Build sorted metadata list so metadata[trigger_index] works
        #

        metadata: List[LocationMetadata] = []
        current_file_index = None
        trigger_index = 0

        location_names = self.build_location_names()
        default_level_lists = self.build_default_level_lists()

        for name_index, files_index, num_levels in LocationMetadataBuilder.LOCATION_METADATA:

            # calculate group_index, map_index_offset
            if current_file_index != files_index:
                current_file_index = files_index
                group_index = 0
                map_index_offset = 0
                next_map_offset = num_levels
            else:
                group_index += 1
                map_index_offset = next_map_offset
                next_map_offset += num_levels

            default_level = default_level_lists[files_index][group_index] - map_index_offset

            meta = LocationMetadata(
                name        = location_names[name_index],
                name_index  = name_index,
                files_index = files_index,
                group_index = group_index,
                
                map_index_offset= map_index_offset,
                num_levels      = num_levels,
                default_level   = default_level,
                trigger_index   = trigger_index
            )
            metadata.append(meta)

            trigger_index += 1

        # NOT OPTIONAL: order of appearance serves as index by trigger_index.
        metadata.sort(key=lambda m: m.trigger_index)
        return metadata

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
        surf = pygame.Surface(tuple(u5map.size_in_tiles.scale(self.tileset.tile_size)))
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

