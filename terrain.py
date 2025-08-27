# file: terrain.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class Terrain:
    walk: bool = False
    climb: bool = False
    horse: bool = False
    carpet: bool = False
    skiff: bool = False
    ship: bool = False

_terrains = None

def get_terrains():
    global _terrains
    if _terrains is None:
                
        # make a list of the 256 terrains all set to false.
        terrains = list(map(lambda _: Terrain(), range(256)))
        
        # walkable terain
        for start, finish in [
            (  4, 12),
            ( 14, 38), # INCLUDES BRIDGE
            ( 44, 45),
            ( 48, 55),
            ( 57, 64),
            ( 68, 69),
            ( 71, 73),
            (106,107), # BRIDGES
            (134,134),
            (140,140), # TRAPDOOR
            (143,147), # INCLUDES LAVA AND CHAIRS
            (170,172), # includes BEDS
            (196,201), # ladders and stairs
            (220,221), # includes moongate
            (227,231),
            (255,255), # the void ????
        ]:
            for i in range(start, finish + 1):
                terrains[i].walk = True
                terrains[i].horse = True
                terrains[i].carpet = True

        # horse refusals
        for i in [
            4,      # swamp
            12,      # mountains
            143,      # lava
        ]:
            terrains[i].horse = False
                
        # horse and carpet refusal
        for start, finish in [
            (144,147),     # chairs
            (171,172),      # bed
            (196,199),      # stairs
            (200,201)      # ladders      
        ]:
            for i in range(start, finish + 1):
                terrains[i].horse = False
                terrains[i].carpet = False
                
        # carpet traversable extras
        for start, finish in [
            (  1,  3), # water (includes ocean)
            ( 96,105), # river
            (108,111), # river heads
        ]:
            for i in range(start, finish + 1):
                terrains[i].carpet = True

        # climbable - only when on foot
        for i in [
            76,    # rock pile
            202,    # fence east-west
            203     # fence north-south
        ]:
            terrains[i].climb = True

        # skiff traversable
        for start, finish in [
            (  1,  3), # water (includes ocean)
            ( 52, 55), # angled beach
            ( 96,105), # river
            (108,111), # river heads
        ]:
            for i in range(start, finish + 1):
                terrains[i].skiff = True

        # ship traversable
        for i in [1,  2]:
            terrains[i].ship = True

        _terrains = terrains

    return _terrains

def can_traverse(transport_mode: str, tile_id: int):
    terrain = get_terrains()[tile_id]
    return getattr(terrain, transport_mode)

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

