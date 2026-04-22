import random

import pytest

from dark_libraries.dark_math import Coord
from data.global_registry import GlobalRegistry
from models.enums.npc_tile_id import NpcTileId
from models.enums.terrain_category import TerrainCategory
from models.global_location import GlobalLocation
from models.npc_metadata import NpcMetadata
from models.terrain import Terrain
from services.monster_spawner import MonsterSpawner


class _FakeSprite:
    def create_random_time_offset(self):
        return 0.0

    def get_current_frame(self, _offset):
        return None


class _FakeU5Map:
    def __init__(self, tile_id: int):
        self._tile_id = tile_id

    def get_tile_id(self, _level_index, _coord):
        return self._tile_id


class _FakeNpcService:
    def __init__(self):
        self._active_npcs = []

    def get_occupied_coords(self):
        return set()

    def add_npc(self, npc):
        self._active_npcs.append(npc)

    def get_npcs(self):
        return {npc.coord: npc for npc in self._active_npcs}


class _FakeMapCacheService:
    def get_blocked_coords(self, _location_index, _level_index, transport_mode):
        return set()


class _FakePartyAgent:
    _spent_action_points = 0


def _build_meta(npc_tile_id: int, overworld: bool, underworld: bool, terrain_categories):
    meta = NpcMetadata(
        name="test",
        npc_tile_id=npc_tile_id,
        general_stats=(10, 10, 10),
        combat_stats=(0, 5, 10),      # armour, damage, hp > 0 (so spawn isn't aborted)
        other_stats=(1, 0.0, 1),
    )
    meta.abilities_terrain.overworld = overworld
    meta.abilities_terrain.underworld = underworld
    meta.abilities_terrain.allowed_terrain_spawns = set(terrain_categories)
    return meta


def _build_spawner(*, monster_specs, tile_id_to_category):
    """
    monster_specs: list of (NpcTileId, overworld, underworld, {TerrainCategory, ...})
    tile_id_to_category: dict[tile_id] -> TerrainCategory | None
                         The map returns the first tile_id for every coord.
    """
    reg = GlobalRegistry()

    map_tile_id = next(iter(tile_id_to_category))
    for tile_id, category in tile_id_to_category.items():
        terrain = Terrain()
        terrain.terrain_category = category
        reg.terrains.register(tile_id, terrain)

    reg.maps.register(0, _FakeU5Map(map_tile_id))

    for npc_tile_id_enum, overworld, underworld, categories in monster_specs:
        reg.npc_metadata.register(
            npc_tile_id_enum.value,
            _build_meta(npc_tile_id_enum.value, overworld, underworld, categories),
        )
        reg.sprites.register(npc_tile_id_enum.value, _FakeSprite())

    spawner = MonsterSpawner()
    spawner.npc_service = _FakeNpcService()
    spawner.map_cache_service = _FakeMapCacheService()
    spawner.global_registry = reg
    spawner.party_agent = _FakePartyAgent()
    return spawner


@pytest.fixture
def force_spawn(monkeypatch):
    # pass the probability gate, pick angle 0 (so translate_polar lands on a deterministic coord),
    # and make random.choice deterministic if the candidate pool has >1 entry.
    monkeypatch.setattr(random, "randint", lambda _a, _b: 1)
    monkeypatch.setattr(random, "uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])


def test_grass_tile_spawns_grass_monster(force_spawn):
    spawner = _build_spawner(
        monster_specs=[(NpcTileId.ORC, True, False, {TerrainCategory.GRASS})],
        tile_id_to_category={5: TerrainCategory.GRASS},
    )

    spawner.pass_time(GlobalLocation(0, 0, Coord[int](50, 50)))

    spawned = spawner.npc_service._active_npcs
    assert len(spawned) == 1
    assert spawned[0].tile_id == NpcTileId.ORC.value


def test_water_tile_with_grass_only_pool_does_not_spawn(force_spawn):
    spawner = _build_spawner(
        monster_specs=[(NpcTileId.ORC, True, False, {TerrainCategory.GRASS})],
        tile_id_to_category={1: TerrainCategory.WATER},
    )

    spawner.pass_time(GlobalLocation(0, 0, Coord[int](50, 50)))

    assert spawner.npc_service._active_npcs == []


def test_overworld_only_monster_does_not_spawn_on_underworld(force_spawn):
    spawner = _build_spawner(
        monster_specs=[(NpcTileId.SHARK, True, False, {TerrainCategory.WATER})],
        tile_id_to_category={1: TerrainCategory.WATER},
    )

    spawner.pass_time(GlobalLocation(0, 255, Coord[int](50, 50)))

    assert spawner.npc_service._active_npcs == []


def test_underworld_monster_spawns_on_underworld(force_spawn):
    spawner = _build_spawner(
        monster_specs=[(NpcTileId.SLIME, False, True, {TerrainCategory.SWAMP})],
        tile_id_to_category={4: TerrainCategory.SWAMP},
    )

    spawner.pass_time(GlobalLocation(0, 255, Coord[int](50, 50)))

    spawned = spawner.npc_service._active_npcs
    assert len(spawned) == 1
    assert spawned[0].tile_id == NpcTileId.SLIME.value


def test_uncategorised_tile_does_not_spawn(force_spawn):
    spawner = _build_spawner(
        monster_specs=[(NpcTileId.ORC, True, True, {TerrainCategory.GRASS})],
        tile_id_to_category={200: None},  # ladder tile — no terrain category
    )

    spawner.pass_time(GlobalLocation(0, 0, Coord[int](50, 50)))

    assert spawner.npc_service._active_npcs == []


def test_only_terrain_matching_monster_spawns_from_mixed_pool(force_spawn):
    spawner = _build_spawner(
        monster_specs=[
            (NpcTileId.SHARK, True, False, {TerrainCategory.WATER}),
            (NpcTileId.ORC,   True, False, {TerrainCategory.GRASS}),
        ],
        tile_id_to_category={5: TerrainCategory.GRASS},
    )

    spawner.pass_time(GlobalLocation(0, 0, Coord[int](50, 50)))

    spawned = spawner.npc_service._active_npcs
    assert len(spawned) == 1
    assert spawned[0].tile_id == NpcTileId.ORC.value


def test_no_spawn_off_overworld_level(force_spawn):
    # location_index != 0 (a town / dungeon) → early return, regardless of pool.
    spawner = _build_spawner(
        monster_specs=[(NpcTileId.ORC, True, True, {TerrainCategory.GRASS})],
        tile_id_to_category={5: TerrainCategory.GRASS},
    )

    spawner.pass_time(GlobalLocation(1, 0, Coord[int](50, 50)))

    assert spawner.npc_service._active_npcs == []
