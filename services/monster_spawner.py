import math
import random

from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from models.global_location import GlobalLocation
from models.enums.npc_ids   import MonsterTileId
from models.monster_state   import MonsterState

from services.map_cache.map_cache_service import MapCacheService
from services.npc_service import NpcService

from .npc_spawner import NpcSpawner

class MonsterSpawner(NpcSpawner, LoggerMixin):

    def __init__(self):
        super().__init__()

    MONSTER_SPAWN_DISTANCE: float = 10
    MONSTER_SPAWN_PROBABILITY: float = 0.1
    MAXIMUM_MONSTER_COUNT = 10

    npc_service: NpcService
    map_cache_service: MapCacheService

    def load_level(self, location_index: int, level_index: int):
        self.location_index = location_index
        self.level_index = level_index

    def set_player_coord(self, player_coord: Coord):
        self.player_coord = player_coord

    def pass_time(self):

        if self.location_index != 0:
            # This is a monster free zone.
            return

        if len(self.npc_service.get_npcs()) >= __class__.MAXIMUM_MONSTER_COUNT:
            # have enough monsters now.
            return

        if random.randint(1,int(1/__class__.MONSTER_SPAWN_PROBABILITY)) > 1:
            # no monsters for you.
            return

        # randomly choose kind of monster
        monster_tile_id_enum = random.choice(list(MonsterTileId))

        # randomly choose location of monster
        blocked_coords = self.map_cache_service.get_blocked_coords(self.location_index, self.level_index, transport_mode_index = 0)
        occupied_coords = self.npc_service.get_occupied_coords()

        monster_coord = self.player_coord # choose an obviously blocked coord
        while monster_coord in blocked_coords.union(occupied_coords):
            monster_coord = self.player_coord.translate_polar(__class__.MONSTER_SPAWN_DISTANCE, random.uniform(-math.pi, math.pi))

        # create monster
        monster_global_location = GlobalLocation(self.location_index, self.level_index, monster_coord)
        monster_state = MonsterState(monster_global_location)
        super()._spawn_npc(monster_tile_id_enum.value, monster_state)

        self.log(f"Spawned {monster_tile_id_enum.name} at {monster_coord}")