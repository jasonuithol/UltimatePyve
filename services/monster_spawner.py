import math
import random

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from data.global_registry import GlobalRegistry
from models.agents.party_agent import PartyAgent
from models.global_location import GlobalLocation
from models.enums.npc_tile_id   import NpcTileId
from models.enums.transport_mode import TransportMode

from models.agents.monster_agent import MonsterAgent
from models.terrain import Terrain
from services.map_cache.map_cache_service import MapCacheService
from services.npc_service import NpcService

class MonsterSpawner(LoggerMixin, DarkEventListenerMixin):

    def __init__(self):
        super().__init__()
        self._party_location: GlobalLocation = None

    MONSTER_SPAWN_RADIUS: float = 10
    MONSTER_SPAWN_PROBABILITY: float = 0.02
    MAXIMUM_MONSTER_COUNT = 10

    npc_service: NpcService
    map_cache_service: MapCacheService
    global_registry: GlobalRegistry
    party_agent: PartyAgent

    def loaded(self, party_location: GlobalLocation):
        self._party_location = party_location

    def _spawn_monster(self, npc_tile_id: int, monster_coord: Coord[int]):
        sprite = self.global_registry.sprites.get(npc_tile_id)
        npc_metadata = self.global_registry.npc_metadata.get(npc_tile_id)
        npc_agent = MonsterAgent(monster_coord, sprite, npc_metadata)
        if npc_agent.maximum_hitpoints == 0:
            self.log("ERROR: Aborting spawning of enemy with 0 maximum hit points to avoid a div/0")
            return
        npc_agent._spent_action_points = self.party_agent._spent_action_points

        self.npc_service.add_npc(npc_agent)

    def pass_time(self, party_location: GlobalLocation):

        self._party_location = party_location

        # This is a monster free zone.
        # TODO: This will prevent dungeon monsters spawning, when dungeons are added.
        if self._party_location.location_index != 0: return

        # have enough monsters now.
        if len(self.npc_service._active_npcs) >= __class__.MAXIMUM_MONSTER_COUNT: return

        # the magic 8-ball said no.
        if random.randint(1,int(1/__class__.MONSTER_SPAWN_PROBABILITY)) > 1: return

        # randomly choose location of monster somewhere on (not in) a circle around the player
        blocked_coords = self.map_cache_service.get_blocked_coords(self._party_location.location_index, self._party_location.level_index, transport_mode = TransportMode.WALK)
        occupied_coords = self.npc_service.get_occupied_coords()

        monster_coord = None
        num_iterations = 0
        while monster_coord is None or monster_coord in blocked_coords.union(occupied_coords):
            num_iterations += 1
            assert num_iterations < 100, "Infinite loop detected"
            monster_coord = self._party_location.coord.translate_polar(__class__.MONSTER_SPAWN_RADIUS, random.uniform(-math.pi, math.pi))

        # Look up the terrain category at the chosen coord.
        u5_map = self.global_registry.maps.get(self._party_location.location_index)
        terrain_tile_id = u5_map.get_tile_id(self._party_location.level_index, monster_coord)
        terrain: Terrain = self.global_registry.terrains.get(terrain_tile_id)
        if terrain is None or terrain.terrain_category is None:
            return
        terrain_category = terrain.terrain_category

        # Scope flag comes from the current level (see docs/SPAWN_RULES.md).
        is_underworld = self._party_location.level_index == 255

        # Filter the spawn pool to NPCs allowed on this scope + terrain.
        candidates: list[NpcTileId] = []
        for npc_tile_id_enum in NpcTileId:
            meta = self.global_registry.npc_metadata.get(npc_tile_id_enum.value)
            if meta is None:
                continue
            terrain_abilities = meta.abilities_terrain
            scope_allowed = terrain_abilities.underworld if is_underworld else terrain_abilities.overworld
            if not scope_allowed:
                continue
            if terrain_category not in terrain_abilities.allowed_terrain_spawns:
                continue
            candidates.append(npc_tile_id_enum)

        if not candidates:
            return

        monster_tile_id_enum = random.choice(candidates)

        # create monster
        self._spawn_monster(monster_tile_id_enum.value, monster_coord)
        self.log(f"Spawned {monster_tile_id_enum.name} at {monster_coord} ({terrain_category.name}), totalling {len(self.npc_service._active_npcs)} (alternate count={len(self.npc_service.get_npcs())}) active monsters")
