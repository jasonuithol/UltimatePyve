# file: location.py
from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path
from u5map import U5Map
from tileset import load_tiles16_raw, ega_palette, TILES16_PATH
from data import DataOVL

LOCATION_WIDTH = 32
LOCATION_HEIGHT = 32
CHUNK_DIM = 16
GRID_DIM = LOCATION_WIDTH // CHUNK_DIM

# Load shared tileset/palette once (raw pixel data, no Surfaces)
_TILESET_RAW = load_tiles16_raw(TILES16_PATH)
_PALETTE = ega_palette

dataOvl = DataOVL.load()
location_names = [p.decode('ascii') for p in dataOvl.city_names_caps.split(b'\x00') if p]

# Append missing names (these are not in city_names_caps)
location_names += [
    "LORD BRITISH'S CASTLE",
    "BLACKTHORN'S CASTLE",
    "SPEKTRAN",
    "SIN'VRAAL'S HUT",
    "GRENDEL'S HUT"
]

FILES = [
    "TOWNE.DAT",
    "CASTLE.DAT",
    "KEEP.DAT",
    "DWELLING.DAT"
]

@dataclass
class LocationMetadata:
    name_index: int
    files_index: int
    map_index_offset: int
    num_levels: int

# LOCATION_METADATA
# key = location_names index
# value = (FILES index, map_index_offset, num_levels)
LOCATION_METADATA = [
    # === TOWNE.DAT ===
    {0: (0, 0, 2)},   # 0  MOONGLOW
    {1: (0, 2, 2)},   # 1  BRITAIN
    {2: (0, 4, 2)},   # 2  JHELOM
    {3: (0, 6, 2)},   # 3  YEW
    {4: (0, 8, 2)},   # 4  MINOC
    {5: (0,10, 2)},   # 5  TRINSIC
    {6: (0,12, 2)},   # 6  SKARA BRAE
    {7: (0,14, 2)},   # 7  NEW MAGINCIA

    # === CASTLE.DAT ===
    {27: (1, 0, 5)},  # 27 LORD BRITISH'S CASTLE
    {28: (1, 5, 5)},  # 28 BLACKTHORN'S CASTLE
    {13: (1,10, 1)},  # 13 WEST BRITANNY
    {14: (1,11, 1)},  # 14 NORTH BRITANNY
    {15: (1,12, 1)},  # 15 EAST BRITANNY
    {16: (1,13, 1)},  # 16 PAWS
    {17: (1,14, 1)},  # 17 COVE
    {18: (1,15, 1)},  # 18 BUCCANEER'S DEN

    # === KEEP.DAT ===
    {19: (2, 0, 2)},  # 19 ARARAT
    {20: (2, 2, 2)},  # 20 BORDERMARCH
    {21: (2, 4, 1)},  # 21 FARTHING
    {22: (2, 5, 1)},  # 22 WINDEMERE
    {23: (2, 6, 1)},  # 23 STONEGATE
    {24: (2, 7, 3)},  # 24 THE LYCAEUM
    {25: (2,10, 3)},  # 25 EMPATH ABBEY
    {26: (2,13, 3)},  # 26 SERPENT'S HOLD

    # === DWELLING.DAT ===
    {8:  (3, 0, 3)},  # 8  FOGSBANE
    {9:  (3, 3, 3)},  # 9  STORMCROW
    {10: (3, 6, 3)},  # 10 GREYHAVEN
    {11: (3, 9, 3)},  # 11 WAVEGUIDE
    {12: (3,12, 1)},  # 12 IOLO'S HUT
    {29: (3,13, 1)},  # 29 SPEKTRAN
    {30: (3,14, 1)},  # 30 SIN'VRAAL'S HUT
    {31: (3,15, 1)}   # 31 GRENDEL'S HUT
]

# Build sorted metadata list so metadata[name_index] works
metadata: List[LocationMetadata] = []
for entry in LOCATION_METADATA:
    name_index = next(iter(entry.keys()))
    files_index, map_index_offset, num_levels = entry[name_index]
    metadata.append(LocationMetadata(name_index, files_index, map_index_offset, num_levels))
metadata.sort(key=lambda m: m.name_index)

def get_location_metadata(location_index: int) -> Tuple[str, str, int, int]:
    name = location_names[location_index]
    meta = metadata[location_index]
    filename = FILES[meta.files_index]
    return name, filename, meta.map_index_offset, meta.num_levels

def load_location_map(location_index: int) -> U5Map:
    name = location_names[location_index]
    meta = metadata[location_index]
    filename = FILES[meta.files_index]
    map_index = meta.map_index_offset
    num_levels = meta.num_levels

    path = Path("u5") / filename
    if not path.exists():
        raise FileNotFoundError(f"Map file not found: {filename}")

    map_size = LOCATION_WIDTH * LOCATION_HEIGHT
    offset = map_index * map_size

    levels = []
    with open(path, "rb") as f:
        f.seek(offset)
        for _ in range(num_levels):
            tile_ids = bytearray(f.read(map_size))
            levels.append(tile_ids)

    return U5Map(
        name=name or f"{path.stem}_{map_index}",
        width=LOCATION_WIDTH,
        height=LOCATION_HEIGHT,
        tileset=_TILESET_RAW,  # raw pixel data
        palette=_PALETTE,
        levels=levels,
        chunk_dim=CHUNK_DIM,
        grid_dim=GRID_DIM
    )

if __name__ == "__main__":
    # Debug/dump mode — safe to import pygame here
    import pygame

    # IMPORTANT: Dont move this import to the top otherwise you'll create a circular dependency.  It's perfectly fine here though.
    from viewer import render_map_to_surface  # your pygame bridge

    pygame.init()

    for location_index in range(len(metadata)):
        name, filename, map_offset, _ = get_location_metadata(location_index)
        u5map = load_location_map(location_index)
        print(f"Loaded map {name} (index={location_index}) from {filename}")
        for level in range(len(u5map.levels)):
            try:
                rendered_surface = render_map_to_surface(u5map, level_ix=level)
            except Exception as e:
                print(f"Error rendering {name} level {level}: {e}")
                raise e
            pygame.image.save(
                rendered_surface,
                f"{filename}_{location_index}_{u5map.name or 'Unknown'}_level_{level}.png"
            )

    pygame.quit()
    print("All maps dumped.")