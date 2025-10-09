from controllers.display_controller import DisplayController
from controllers.party_controller import PartyController
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.location_metadata import LocationMetadata
from models.npc_agent import NpcAgent
from models.party_state import PartyState
from models.u5_map import U5Map
from services.combat_map_service import CombatMapService
from services.map_cache.map_cache_service import MapCacheService
from services.npc_service import NpcService

COMBAT_MAP_LOCATION_INDEX = -666

class CombatController(LoggerMixin):
    
    # Injectable
    global_registry: GlobalRegistry
    combat_map_service: CombatMapService
    map_cache_service: MapCacheService
    party_state: PartyState
    npc_service: NpcService

    display_controller: DisplayController
    party_controller: PartyController

    def enter_combat(self, enemy_npc: NpcAgent):

        party_transport_mode_index, _ = self.party_state.get_transport_state()

        combat_map = self.combat_map_service.get_combat_map(
            self.party_state.get_current_location(),
            party_transport_mode_index,
            enemy_npc
        )

        combat_map_wrapper = U5Map(
            {0:combat_map},
            LocationMetadata(
                location_index = COMBAT_MAP_LOCATION_INDEX, # index of the location for things like WorldLootLoader, and GlobalLocation references.
                name = "COMBAT",                            # name of the location

                name_index       = None, # which name the location takes.
                files_index      = None, # which file the location is in
                group_index      = None, # order of appearance of the town in the file. Use for indexing into DATA.OVL properties.
                map_index_offset = None, # how many levels to skip to start reading the first level of the location.

                num_levels    = 0,       # how many levels the location contains
                default_level = 0,       # which level the player spawns in when entering the location.
                trigger_index = None,    # the index the entry triggers for this location are at.
                sound_track   = None     # an absolute path to the soundtrack                
            )
        )

        # TODO: Remove this
        self.global_registry.maps.register(combat_map_wrapper.location_index, combat_map_wrapper)
        
        self.map_cache_service.cache_u5map(combat_map_wrapper)

        self.party_controller.enter_combat()

#        self.display_controller.set_active_map(combat_map_wrapper.location_index, 0)
        return
        self.party_controller.exit_combat()

        self.npc_service.remove_npc(enemy_npc)

        self.log("Combat Over !")


    