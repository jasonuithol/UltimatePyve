import math
import random

from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from models.global_location import GlobalLocation
from models.enums.npc_ids   import NpcTileId

from models.terrain import Terrain
from services.map_cache.map_cache_service import MapCacheService
from services.npc_service import NpcService

from .npc_spawner import NpcSpawner

class MonsterSpawner(NpcSpawner, LoggerMixin):

    def __init__(self):
        super().__init__()

    MONSTER_SPAWN_RADIUS: float = 10
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

        # This is a monster free zone.
        # TODO: This will prevent dungeon monsters spawning, when dungeons are added.
        if self.location_index != 0: return

        # have enough monsters now.
        if len(self.npc_service._active_npcs) >= __class__.MAXIMUM_MONSTER_COUNT: return

        # the magic 8-ball said no.
        if random.randint(1,int(1/__class__.MONSTER_SPAWN_PROBABILITY)) > 1: return

        # randomly choose location of monster somewhere on (not in) a circle around the player
        blocked_coords = self.map_cache_service.get_blocked_coords(self.location_index, self.level_index, transport_mode_index = 0)
        occupied_coords = self.npc_service.get_occupied_coords()

        monster_coord = None
        while monster_coord is None or monster_coord in blocked_coords.union(occupied_coords):
            monster_coord = self.player_coord.translate_polar(__class__.MONSTER_SPAWN_RADIUS, random.uniform(-math.pi, math.pi))
        monster_global_location = GlobalLocation(self.location_index, self.level_index, monster_coord)

        # randomly choose kind of monster (that can live on monster_global_location)
        coord_contents = self.map_cache_service.get_location_contents(monster_global_location)
        u5_map = self.global_registry.maps.get(self.location_index)
        terrain_tile_id = u5_map.get_tile_id(self.level_index, monster_coord)
        terrain: Terrain = self.global_registry.terrains.get(terrain_tile_id)

        #
        # TODO: limit the monster selection to those appropriate for the terrain.
        #
        terrain_appropriate_monsters = list(NpcTileId)

        monster_tile_id_enum = random.choice(terrain_appropriate_monsters)


        # create monster
        super()._spawn_npc(monster_tile_id_enum.value, monster_global_location)
        self.log(f"Spawned {monster_tile_id_enum.name} at {monster_coord}, totalling {len(self.npc_service._active_npcs)} (alternate count={len(self.npc_service.get_npcs())}) active monsters")
