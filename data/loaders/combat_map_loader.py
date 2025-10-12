from pathlib import Path
from dark_libraries.dark_math import Coord, Size
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from data.registries.registry_base import Registry
from models.combat_map import CombatMap, DungeonRoom, DungeonRoomTileTrigger, NESWSpawnCoordinateTuple, SpawnCoordinates

ROW_BYTES_PADDED = 32
ROW_BYTES_ACTUAL = 1
NUM_COLS = 11
NUM_ROWS = 11

DIR_NORTH = 0
DIR_EAST  = 1
DIR_SOUTH = 2
DIR_WEST  = 3

ROW_INDEX_EAST  = 1 
ROW_INDEX_WEST  = 2
ROW_INDEX_SOUTH = 3
ROW_INDEX_NORTH = 4

ROW_INDEX_MONSTER_TILES = 5

ROW_INDEX_MONSTER_X = 6
ROW_INDEX_MONSTER_Y = 7

ROW_INDEX_TRIGGER_TILES = 0
ROW_INDEX_TRIGGER_COORD = 8
ROW_INDEX_TRIGGER_RESULT_1_COORD = 9
ROW_INDEX_TRIGGER_RESULT_2_COORD = 10

NUM_PARTY_SPAWNS = 6
NUM_MONSTER_SPAWNS = 16
NUM_TRIGGERS = 8

class CombatMapLoader(LoggerMixin):

    global_registry: GlobalRegistry

    @classmethod
    def _to_map_byte_offset(cls, map_index: int) -> int:
        return map_index * NUM_ROWS * ROW_BYTES_PADDED

    def _load_map(self, map_index: int, data: bytes, is_dungeon_room: bool) -> CombatMap:
        map_byte_offset = __class__._to_map_byte_offset(map_index)
        map_tile_ids = dict[Coord, int]()
        # Load basic tile info
        for row_index in range(NUM_ROWS):
            row_offset = map_byte_offset + (row_index * ROW_BYTES_PADDED)
            for col_index in range(NUM_COLS):
                tile_id = int(data[row_offset + col_index])
                map_tile_ids[Coord(col_index, row_index)] = tile_id

        def _to_row_extra_offset(row_index: int) -> int:
            return __class__._to_map_byte_offset(map_index) + (row_index * ROW_BYTES_PADDED) + NUM_COLS

        # party spawn coords
        def _read_spawn_coords(row_index: int):
            row_extra_offset = _to_row_extra_offset(row_index)
            for party_spawn_index in range(NUM_PARTY_SPAWNS):
                yield Coord(
                    data[row_extra_offset + party_spawn_index],
                    data[row_extra_offset + party_spawn_index + NUM_PARTY_SPAWNS]
                )

        party_spawn_coords: NESWSpawnCoordinateTuple = (
            # Must be in this exact order: NESW
            SpawnCoordinates(_read_spawn_coords(ROW_INDEX_NORTH)),
            SpawnCoordinates(_read_spawn_coords(ROW_INDEX_EAST)),
            SpawnCoordinates(_read_spawn_coords(ROW_INDEX_SOUTH)),
            SpawnCoordinates(_read_spawn_coords(ROW_INDEX_WEST))
        )

        # Monster spawn coords
        monster_spawn_coords: SpawnCoordinates = tuple(
            Coord(
                data[_to_row_extra_offset(ROW_INDEX_MONSTER_X) + monster_spawn_index],
                data[_to_row_extra_offset(ROW_INDEX_MONSTER_Y) + monster_spawn_index],
            )
            for monster_spawn_index in range(NUM_MONSTER_SPAWNS)
        )

        if is_dungeon_room == True:
            constructor = DungeonRoom
        else:
            constructor = CombatMap

        combat_map = constructor(
            data                 = map_tile_ids,
            size                 = Size(NUM_COLS, NUM_ROWS),
            party_spawn_coords   = party_spawn_coords,
            monster_spawn_coords = monster_spawn_coords
        )

        if is_dungeon_room == True: 
            # This is no longer a simple combat map, but a much more complex and arranged DUNGEON ROOM.
            dungeon_room = combat_map
            del combat_map
        else:
            # For random encounter combat maps, we are D U N
            return combat_map

        #
        # OnlyDungeons from here on in.
        #

        # Static monster tile ids - for set-piece dungeon rooms.
        for monster_spawn_index in range(NUM_MONSTER_SPAWNS):
            dungeon_room.add_static_spawn(
                monster_spawn_coord_index = monster_spawn_index, 
                monster_tile_id           = data[_to_row_extra_offset(ROW_INDEX_MONSTER_TILES) + monster_spawn_index]
            )

        # Tile triggers - for set-piece dungeon rooms.
        for trigger_index in range(NUM_TRIGGERS):
            dungeon_room.add_trigger(DungeonRoomTileTrigger(
                trigger_coord = Coord(
                    data[_to_row_extra_offset(ROW_INDEX_TRIGGER_COORD) + trigger_index],
                    data[_to_row_extra_offset(ROW_INDEX_TRIGGER_COORD) + trigger_index + NUM_TRIGGERS],
                ),
                revealed_coord1 = Coord(
                    data[_to_row_extra_offset(ROW_INDEX_TRIGGER_RESULT_1_COORD) + trigger_index],
                    data[_to_row_extra_offset(ROW_INDEX_TRIGGER_RESULT_1_COORD) + trigger_index + NUM_TRIGGERS],
                ),
                revealed_coord2 = Coord(
                    data[_to_row_extra_offset(ROW_INDEX_TRIGGER_RESULT_2_COORD) + trigger_index],
                    data[_to_row_extra_offset(ROW_INDEX_TRIGGER_RESULT_2_COORD) + trigger_index + NUM_TRIGGERS],
                ),
                revealed_tile_id = data[_to_row_extra_offset(ROW_INDEX_TRIGGER_TILES) + trigger_index]
            ))

        return dungeon_room

    def _load_file(self, path: Path, target_collection: Registry[int, CombatMap], are_dungeon_rooms: bool):
        data = path.read_bytes()
        map_index = 0
        while self._to_map_byte_offset(map_index) < len(data):

            combat_map = self._load_map(map_index, data, are_dungeon_rooms)

            target_collection.register(key = map_index, value = combat_map)
            map_index += 1
        self.log(f"Registered {map_index} {'dungeon rooms' if are_dungeon_rooms else 'combat maps'} from {path}")

    def load(self):
        self._load_file(Path("u5/BRIT.CBT"   ), self.global_registry.combat_maps,   are_dungeon_rooms = False)
        self._load_file(Path("u5/DUNGEON.CBT"), self.global_registry.dungeon_rooms, are_dungeon_rooms = True)
        