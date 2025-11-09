# file: terrain.py
from dataclasses import dataclass

from models.enums.terrain_category import TerrainCategory

@dataclass
class Terrain:

    terrain_category: TerrainCategory = None

    walk: bool = False
    horse: bool = False
    carpet: bool = False
    skiff: bool = False
    ship: bool = False
    sail: bool = False

    move_up: bool = False
    move_down: bool = False
    stairs: bool = False

    climb: bool = False
    grapple: bool = False

    emits_light: bool = False
    blocks_light: bool = False
    windowed: bool = False

    entry_point: bool = False
    
'''
moveable_tiles = [
     91,    # pot plant
    144,    # chair north
    145,    # chair east
    146,    # chair south
    147,    # chair west
    165,    # large desk
    166,    # upright barrel
    174,    # small table
    175,    # foot locker,
    180,    # cannon north
    181,    # cannon east
    182,    # cannon south
    183,    # cannon west
]

'''
