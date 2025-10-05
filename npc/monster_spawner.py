import math
import random

from dark_libraries.dark_math import Coord
from items.global_location import GlobalLocation

from .npc_ids import MonsterTileId
from .npc_spawner import NpcSpawner
from .monster_state import MonsterState

class MonsterSpawner(NpcSpawner):

    def __init__(self):
        pass

    MONSTER_SPAWN_DISTANCE: float = 10
    MONSTER_SPAWN_PROBABILITY: float = 0.1

    def load_level(self, location_index: int, level_index: int):
        self.location_index = location_index
        self.level_index = level_index

    def set_player_coord(self, player_coord: Coord):
        self.player_coord = player_coord

    def pass_time(self):

        if random.randint(1,int(1/__class__.MONSTER_SPAWN_PROBABILITY)) > 1:
            # no monsters for you.
            return
        
        monster_tile_id_enum = random.choice(list(MonsterTileId))
        monster_coord = self.player_coord.translate_polar(__class__.MONSTER_SPAWN_DISTANCE, random.uniform(-math.pi, math.pi))
        monster_global_location = GlobalLocation(self.location_index, self.level_index, monster_coord)
        monster_state = MonsterState(monster_global_location)

        super()._spawn_npc(monster_tile_id_enum.value, monster_state)
        print(f"[monster_spawner] Spawned {monster_tile_id_enum.name} at {monster_coord}")