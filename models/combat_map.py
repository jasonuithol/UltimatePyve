from dark_libraries.dark_math import Coord, Size
from models.u5_map_level      import U5MapLevel

SpawnCoordinates = tuple[Coord,...]

# indexed by 0=North, 1=East, 2=South, 3=West, then by party member index.
NESWSpawnCoordinateTuple = tuple[
    SpawnCoordinates,
    SpawnCoordinates,
    SpawnCoordinates,
    SpawnCoordinates
]

class CombatMap(U5MapLevel):
    def __init__(self, data: dict[Coord, int], size: Size, party_spawn_coords: NESWSpawnCoordinateTuple, monster_spawn_coords: SpawnCoordinates):
        super().__init__(data, size)

        self._party_spawn_coords   = party_spawn_coords    
        self._monster_spawn_coords = monster_spawn_coords

class DungeonRoomTileTrigger:
    def __init__(self, trigger_coord: Coord, revealed_coord1: Coord, revealed_coord2: Coord, revealed_tile_id: int):
        self._trigger_coord     = trigger_coord, 
        self._revealed_coord1   = revealed_coord1, 
        self._revealed_coord2   = revealed_coord2, 
        self._revealed_tile_id  = revealed_tile_id

class DungeonRoom(CombatMap):
    
    def __init__(self, data: dict[Coord, int], size: Size, party_spawn_coords: NESWSpawnCoordinateTuple, monster_spawn_coords: SpawnCoordinates):
        super().__init__(data, size, party_spawn_coords, monster_spawn_coords)

        self._static_monster_tile_ids = dict[int, int]() # black magic lives here.
        self._triggers = dict[Coord, DungeonRoomTileTrigger]()

    def add_static_spawn(self, monster_spawn_coord_index: int, monster_tile_id: int):
        self._static_monster_tile_ids[monster_spawn_coord_index] = monster_tile_id

    def get_static_spawns(self) -> dict[Coord, int]:
        return {
            self._monster_spawn_coords[monster_spawn_coord_index] : monster_tile_id
            for monster_spawn_coord_index, monster_tile_id in self._static_monster_tile_ids
        }

    def add_trigger(self, trigger: DungeonRoomTileTrigger):
        self._triggers[trigger._trigger_coord] = trigger

    def get_trigger(self, coord) -> DungeonRoomTileTrigger:
        return self._triggers.get(coord, None)
