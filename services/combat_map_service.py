from dark_libraries.logging import LoggerMixin
from data.global_registry   import GlobalRegistry

from models.global_location import GlobalLocation
from models.npc_agent       import NpcAgent
from models.terrain         import Terrain
from models.u5_map          import U5Map

# CombatMap indexes
COMBAT_MAP_CAMPSITE    = 0
COMBAT_MAP_SWAMP       = 1
COMBAT_MAP_GRASS       = 2
COMBAT_MAP_SCRUB       = 3
COMBAT_MAP_DESERT      = 4
COMBAT_MAP_FOREST      = 5
COMBAT_MAP_MOUNTAINS   = 6
COMBAT_MAP_BRIDGE      = 7
COMBAT_MAP_COBBLESTONE = 8
COMBAT_MAP_CORRIDOR    = 9
COMBAT_MAP_SHADOWLORD  = 10

COMBAT_MAP_SHIP_IN_OCEAN                 = 11
COMBAT_MAP_SHIP_ATTACKING_SHIP_FROM_LAND = 12
COMBAT_MAP_SHIP_ATTACKING_LAND_FROM_SHIP = 13
COMBAT_MAP_SHIP_TO_SHIP                  = 14

COMBAT_MAP_SHORELINE   = 15

TILE_ID_DEEP_OCEAN = 1
TILE_ID_OCEAN = 2

TILE_ID_SWAMP  = 4
TILE_ID_GRASS  = 5
TILE_ID_SCRUB1 = 6
TILE_ID_SAND   = 7
TILE_ID_SCRUB2 = 8
TILE_ID_TREES  = 9
TILE_ID_FOREST = 10

TILE_ID_FOOTHILLS1 = 11
TILE_ID_MOUNTAIN   = 12
TILE_ID_FOOTHILLS2 = 14
TILE_ID_FOOTHILLS3 = 15

TILE_ID_CACTUS = 47

map_to_terrain_dict = {
    COMBAT_MAP_SWAMP:     [TILE_ID_SWAMP],
    COMBAT_MAP_SCRUB:     [TILE_ID_SCRUB1, TILE_ID_SCRUB2],
    COMBAT_MAP_DESERT:    [TILE_ID_SAND, TILE_ID_CACTUS, 28], # added mirage/oasis
    COMBAT_MAP_FOREST:    [TILE_ID_TREES, TILE_ID_FOREST],
    COMBAT_MAP_MOUNTAINS: [TILE_ID_FOOTHILLS1, TILE_ID_FOOTHILLS2, TILE_ID_FOOTHILLS3, TILE_ID_MOUNTAIN, 22, 23, 24], # added dungeon entrances
    COMBAT_MAP_BRIDGE:    [106, 107] # ns and ew bridges
}

terrain_to_map_dict = {
    terrain_tile_id : combat_map_index
    for combat_map_index, terrain_tile_id_list in map_to_terrain_dict.items()
        for terrain_tile_id in terrain_tile_id_list
}

# tile_ids
PIRATE     = 300
SHADOWLORD = 508

class CombatMapService(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def _get_combat_map_index(self, player_location: GlobalLocation, transport_mode_index: int, enemy_npc_agent: NpcAgent):

        assert transport_mode_index != 3, "Cannot enter combat in a skiff."

        u5_map: U5Map = self.global_registry.maps.get(player_location.location_index)
        enemy_terrain_tile_id = u5_map.get_tile_id(player_location.level_index, enemy_npc_agent.get_coord())
        enemy_terrain: Terrain = self.global_registry.terrains.get(enemy_terrain_tile_id)
        enemy_terrain_is_water = enemy_terrain.walk == False and (enemy_terrain.skiff == True or enemy_terrain.ship == True)

        #
        # TODO: Campsite combat.  Maybe a function of a camping service
        #

        if enemy_npc_agent.tile_id == SHADOWLORD: return COMBAT_MAP_SHADOWLORD

        # TODO: Find the trigger for the Corridor CombatMap
        if player_location.is_in_town(): return          COMBAT_MAP_COBBLESTONE

        # party using land transport
        if transport_mode_index in [0,1,2]:

            if enemy_npc_agent.tile_id == PIRATE: return COMBAT_MAP_SHIP_ATTACKING_SHIP_FROM_LAND

            # Terrain dict based ?
            combat_map_index = terrain_to_map_dict.get(enemy_terrain_tile_id, None)

            if not combat_map_index is None: return      combat_map_index
        
            if enemy_terrain_is_water: return            COMBAT_MAP_SHORELINE

            # default
            return                                       COMBAT_MAP_GRASS

        # party on ship
        elif transport_mode_index in [4,5]:

            if enemy_npc_agent.tile_id == PIRATE: return COMBAT_MAP_SHIP_TO_SHIP
            elif enemy_terrain_is_water: return          COMBAT_MAP_SHIP_IN_OCEAN
            return                                       COMBAT_MAP_SHIP_ATTACKING_LAND_FROM_SHIP
        
        #
        # TODO: Dungeon combat
        #
        
    def get_combat_map(self, player_location: GlobalLocation, transport_mode_index: int, enemy_npc_agent: NpcAgent):
         combat_map_index = self._get_combat_map_index(player_location, transport_mode_index, enemy_npc_agent)
         return self.global_registry.combat_maps.get(combat_map_index)

    