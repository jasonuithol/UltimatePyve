# file: location.py

#
# INNER LOCATIONS (i.e. TOWNES KEEPS CASTLES DWELLINGS)   TODO: DUNGEONS
#

from typing import List
from pathlib import Path
from game.u5map import U5Map, LocationMetadata
from loaders.tileset import load_tileset
from loaders.data import DataOVL
from dark_libraries.dark_math import Coord, Size

LOCATION_WIDTH = 32
LOCATION_HEIGHT = 32
CHUNK_DIM = 16
GRID_DIM = LOCATION_WIDTH // CHUNK_DIM

# Load shared tileset/palette once (raw pixel data, no Surfaces)
_TILESET = load_tileset()

dataOvl = DataOVL.load()
_location_names = [p.decode('ascii') for p in dataOvl.city_names_caps.split(b'\x00') if p]

# Append missing names (these are not in city_names_caps)
_location_names += [
    "LORD BRITISH'S CASTLE",
    "BLACKTHORN'S CASTLE",
    "SPEKTRAN",
    "SIN'VRAAL'S HUT",
    "GRENDEL'S HUT"
]

FILES = [
    "TOWNE.DAT",
    "DWELLING.DAT",
    "CASTLE.DAT",
    "KEEP.DAT"
]

DEFAULT_LEVEL_LISTS = [
    DataOVL.load().map_index_towne,
    DataOVL.load().map_index_dwelling,
    DataOVL.load().map_index_castle,
    DataOVL.load().map_index_keep
]

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

def build_metadata():

    # Build sorted metadata list so metadata[location_index] works
    metadata: List[LocationMetadata] = []
    current_file_index = None
    trigger_index = 0

    for name_index, files_index, num_levels in LOCATION_METADATA:

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

        default_level = DEFAULT_LEVEL_LISTS[files_index][group_index] - map_index_offset

        meta = LocationMetadata(
            name=_location_names[name_index],
            name_index=name_index,
            files_index=files_index,
            group_index=group_index,
            
            map_index_offset=map_index_offset,
            num_levels=num_levels,
            default_level=default_level,
            trigger_index=trigger_index
        )
        metadata.append(meta)

        trigger_index += 1

    metadata.sort(key=lambda m: m.trigger_index)

    return metadata

_metadata = None

def get_metadata():
    global _metadata
    if _metadata is None:
        _metadata = build_metadata()
    return _metadata

def load_location_map(trigger_index: int) -> U5Map:
    meta = get_metadata()[trigger_index]
    filename = FILES[meta.files_index]

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
        name=meta.name,
        size_in_tiles=Size(LOCATION_WIDTH,LOCATION_HEIGHT),
        tileset=_TILESET,  # raw pixel data
        levels=levels,
        chunk_dim=CHUNK_DIM,
        grid_dim=GRID_DIM,
        location_metadata=meta
    )

def render_location_map_to_disk(u5map: U5Map, level: int) -> U5Map:
    import pygame
    from loaders.tileset import Tile
    pygame.init()
    surf = pygame.Surface(tuple(u5map.size_in_tiles.scale(_TILESET.tile_size)))
    for x in range(u5map.size_in_tiles.x):
        for y in range(u5map.size_in_tiles.y):
            tile_id = u5map.get_tile_id(level, x, y)
            tile: Tile = _TILESET.tiles[tile_id]
            tile.blit_to_surface(surf, Coord(x * _TILESET.tile_size, y * _TILESET.tile_size))
    pygame.image.save(
        surf,
        f"{u5map.name}_{level}.png"
    )
    pygame.quit()

    return surf

if __name__ == "__main__":
    metadata = get_metadata()
    for ix in range(len(metadata)):
        meta = metadata[ix]
        name, filename, map_offset = meta.name, FILES[meta.files_index], meta.map_index_offset

        u5map: U5Map = load_location_map(meta.trigger_index)
        print(f"Loaded map {name} (index={ix}) from {filename}")
        for level in range(len(u5map.levels)):
            try:
                surf = render_location_map_to_disk(u5map, level)
            except Exception as e:
                print(f"Error rendering {name!r} level {level!r}: {e}")
                raise e
    print("All maps dumped.")