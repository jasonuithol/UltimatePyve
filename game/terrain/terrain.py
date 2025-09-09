# file: terrain.py
from dataclasses import dataclass

@dataclass
class Terrain:
    walk: bool = False
    climb: bool = False
    horse: bool = False
    carpet: bool = False
    skiff: bool = False
    ship: bool = False
    sail: bool = False

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
