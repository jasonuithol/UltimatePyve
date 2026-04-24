import pytest

from data.global_registry import GlobalRegistry
from data.loaders.npc_metadata_loader import NpcMetadataLoader
from models.enums.npc_tile_id import NpcTileId


@pytest.fixture(scope="module")
def metadata_registry():
    loader = NpcMetadataLoader()
    loader.global_registry = GlobalRegistry()
    loader.load()
    return loader.global_registry.npc_metadata


def _abilities(registry, npc_tile_id: NpcTileId):
    return registry.get(npc_tile_id.value).abilities_terrain


#
# Underworld-only per design: mongbat, corpser (and the previously-existing
# underworld-only crew).
#
@pytest.mark.parametrize(
    "npc_tile_id",
    [
        NpcTileId.MONGBAT,
        NpcTileId.CORPSER,
        NpcTileId.DAEMON,
        NpcTileId.SLIME,
        NpcTileId.GIANT_RAT,
        NpcTileId.BAT,
        NpcTileId.GHOST,
        NpcTileId.GAZER,
        NpcTileId.ROTWORM,
    ],
)
def test_underworld_only_monsters(metadata_registry, npc_tile_id):
    abilities = _abilities(metadata_registry, npc_tile_id)
    assert abilities.overworld  is False
    assert abilities.underworld is True


#
# Dungeon-only monsters: never wilderness-spawned. GREMLIN will also be
# a campsite ambusher once campsites are implemented.
#
@pytest.mark.parametrize(
    "npc_tile_id",
    [
        NpcTileId.GARGOYLE,
        NpcTileId.REAPER,
        NpcTileId.MIMIC,
        NpcTileId.GREMLIN,
    ],
)
def test_dungeon_only_monsters_have_no_wilderness_spawn(metadata_registry, npc_tile_id):
    abilities = _abilities(metadata_registry, npc_tile_id)
    assert abilities.overworld  is False
    assert abilities.underworld is False
    assert abilities.allowed_terrain_spawns == set()


#
# Surface + underworld land-dwellers that SHOULD still roam the wilderness.
#
@pytest.mark.parametrize(
    "npc_tile_id",
    [
        NpcTileId.ORC,
        NpcTileId.SKELETON,
        NpcTileId.TROLL,
        NpcTileId.DRAGON,
    ],
)
def test_overworld_land_dwellers_still_spawn_overworld(metadata_registry, npc_tile_id):
    abilities = _abilities(metadata_registry, npc_tile_id)
    assert abilities.overworld  is True
    assert abilities.underworld is True


#
# Sea creatures: overworld water only.
#
@pytest.mark.parametrize(
    "npc_tile_id",
    [
        NpcTileId.SHARK,
        NpcTileId.SEA_HORSE,
        NpcTileId.SQUID,
        NpcTileId.SEA_SERPENT,
    ],
)
def test_sea_creatures_overworld_only(metadata_registry, npc_tile_id):
    abilities = _abilities(metadata_registry, npc_tile_id)
    assert abilities.overworld  is True
    assert abilities.underworld is False
