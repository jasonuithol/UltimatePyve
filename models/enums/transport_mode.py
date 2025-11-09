from enum import Enum

from models.terrain import Terrain

class TransportDirection(Enum):
    NORTH = 0
    EAST  = 1
    SOUTH = 2
    WEST  = 3

class NpcTransportTileId(Enum):

    UNMOUNTED_HORSE_EAST = 272
    UNMOUNTED_HORSE_WEST = 273

    PIRATE_NORTH = 300
    PIRATE_EAST  = 301
    PIRATE_SOUTH = 302
    PIRATE_WEST  = 303

class PlayerTransportTileId(Enum):

    HORSE_EAST = 274
    HORSE_WEST = 275

    CARPET_EAST = 276
    CARPET_WEST = 277

    SAIL_NORTH = 288
    SAIL_EAST  = 289
    SAIL_SOUTH = 290
    SAIL_WEST  = 291

    SHIP_NORTH = 292
    SHIP_EAST  = 293
    SHIP_SOUTH = 294
    SHIP_WEST  = 295

    SKIFF_NORTH = 296
    SKIFF_EAST  = 297
    SKIFF_SOUTH = 298
    SKIFF_WEST  = 299

class TransportMode(Enum):

    WALK   = 0
    HORSE  = 1
    CARPET = 2

    SKIFF  = 3
    SHIP   = 4
    SAIL   = 5

    def can_traverse(self, terrain: Terrain) -> bool:
        return getattr(terrain, self.name.lower())

class TransportDirectionality(Enum):
    EastWest           = 0
    NorthEastSouthWest = 1

TRANSPORT_DIRECTIONALITY_MAP = {
    TransportMode.HORSE  : TransportDirectionality.EastWest,
    TransportMode.CARPET : TransportDirectionality.EastWest,
    TransportMode.SAIL   : TransportDirectionality.NorthEastSouthWest,
    TransportMode.SHIP   : TransportDirectionality.NorthEastSouthWest,
    TransportMode.SKIFF  : TransportDirectionality.NorthEastSouthWest
}

TRANSPORT_MODE_DEXTERITY_MAP = {
    TransportMode.WALK   : 15, # walk
    TransportMode.HORSE  : 20, # horse
    TransportMode.CARPET : 25, # carpet
    TransportMode.SKIFF  : 10, # skiff
    TransportMode.SHIP   : 15, # ship
    TransportMode.SAIL   : 25  # sail
}