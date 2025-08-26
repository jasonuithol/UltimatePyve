# location.py
from dataclasses import dataclass
import pygame

from typing import Dict, Tuple
from pathlib import Path
from u5map import U5Map
from tileset import load_tiles16, ega_palette  # your existing tileset/palette loader
from data import DataOVL

LOCATION_WIDTH = 32
LOCATION_HEIGHT = 32
CHUNK_DIM = 16
GRID_DIM = LOCATION_WIDTH // CHUNK_DIM

# Load shared tileset/palette once
_TILESET, _PALETTE = load_tiles16("u5/TILES.16"), ega_palette

dataOvl = DataOVL.load()
location_names = [p.decode('ascii') for p in dataOvl.city_names_caps.split(b'\x00') if p]

# for some reason, these don't appear in city_names_caps.
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

# List[Dict[int,Tuple[int,int,int]]]
# list order unimportant
# Dicts are: key=all_location_name index, value=(FILES index, map_index_offset, number of levels)
LOCATION_METADATA = [
    # TOWNE.DAT
    {0: (0, 0,2)},   # MOONGLOW
    {1: (0, 2,2)},   # BRITAIN
    {2: (0, 4,2)},   # JHELOM
    {3: (0, 6,2)},   # YEW
    {4: (0, 8,2)},   # MINOC
    {5: (0,10,2)},   # TRINSIC
    {6: (0,12,2)},   # SKARA BRAE
    {7: (0,14,2)},   # NEW MAGINCIA

    # CASTLE.DAT
    {27: (1, 0,5)},  # LORD BRITISH'S CASTLE
    {28: (1, 5,5)},  # BLACKTHORN'S CASTLE
    {13: (1,10,1)},  # WEST BRITANNY
    {14: (1,11,1)},  # NORTH BRITANNY
    {15: (1,12,1)},  # WEST BRITANNY again
    {16: (1,13,1)},  # PAWS
    {17: (1,14,1)},  # COVE
    {18: (1,15,1)},  # BUCCANEER'S DEN

    # KEEP.DAT
    {19: (2, 0,2)},  # ARARAT
    {20: (2, 2,2)},  # BORDERMARCH
    {21: (2, 4,1)},  # FARTHING
    {22: (2, 5,1)},  # WINDEMERE
    {23: (2, 6,1)},  # STONEGATE
    {24: (2, 7,3)},  # THE LYCAEUM
    {25: (2,10,3)},  # EMPATH ABBEY
    {26: (2,13,3)},  # SERPENT'S HOLD

    # DWELLING.DAT
    {8:  (3, 0,3)},  # FOGSBANE
    {9:  (3, 3,3)},  # STORMCROW
    {10: (3, 6,3)},  # GREYHAVEN
    {11: (3, 9,3)},  # WAVEGUIDE
    {12: (3,10,1)},  # IOLO'S HUT
    {29: (3,11,1)},  # SPEKTRAN
    {30: (3,12,1)},  # SIN'VRAAL'S HUT
    {31: (3,13,1)}   # GRENDEL'S HUT
]

@dataclass
class LocationMetadata:
    name_index: int
    files_index: int
    map_index_offset: int
    num_levels: int

metadata = []
for entry in LOCATION_METADATA:
    name_index = next(iter(entry.keys()))
    files_index, map_index_offset, num_levels = entry[name_index]
    metadata.append(
        LocationMetadata(
            name_index=name_index,
            files_index=files_index,
            map_index_offset=map_index_offset,
            num_levels=num_levels
        )
    )

# This allows us to pull an entry with name_index by metadata[name_index]
metadata.sort(key=lambda meta: meta.name_index)

def get_location_metadata(location_index: int) -> Tuple[str,str,int,int]:
    name = location_names[location_index]
    meta = metadata[location_index]
    filename = FILES[meta.files_index]
    map_index = meta.map_index_offset
    num_levels = meta.num_levels
    return name, filename, map_index, num_levels

def load_location_map(location_index: int) -> U5Map:

    name = location_names[location_index]
    meta = metadata[location_index]
    filename = FILES[meta.files_index]
    map_index = meta.map_index_offset
    num_levels = meta.num_levels

    """
    Load a location map from the given .DAT file and submap index.
    Returns a ready-to-use U5Map instance.
    """
    path = Path("u5/" + filename)
    if not path.exists():
        raise FileNotFoundError(f"Map file not found: {filename}")

    # Each map is width*height bytes long
    map_size = LOCATION_WIDTH * LOCATION_HEIGHT
    offset = map_index * map_size

    with open(path, "rb") as f:
        f.seek(offset)
        levels = []
        for _ in range(num_levels):
            tile_ids = bytearray(f.read(map_size))
            levels.append(tile_ids)

    return U5Map(
        name=name or f"{path.stem}_{map_index}",
        width=LOCATION_WIDTH,
        height=LOCATION_HEIGHT,
        tileset=_TILESET,
        palette=_PALETTE,
        levels=levels,
        chunk_dim=CHUNK_DIM,
        grid_dim=GRID_DIM
    )

if __name__ == "__main__":

    for location_index in range(len(metadata)):
        _, filename, map_offset, _ = get_location_metadata(location_index)
        u5map = load_location_map(location_index)
        print(f"Loaded map with location_ix={location_index}, levels={len(u5map.levels)} from {filename}")
        for level in range(len(u5map.levels)):
            try:
                rendered_surface = u5map.render(level) 
            except Exception as e:
                print(f"Error rendering map {u5map.name}({location_index}) at map offset {map_offset}, level {level} for location {location_index} from file {filename}: {e}")
                continue
            pygame.image.save(
                rendered_surface, 
                f"{filename}_{location_index}_{u5map.name or 'Unknown'}_level_{level}.png"
            )

    # If dungeons have their own table, add them here

    pygame.quit()
    print(f"All maps dumped.")

