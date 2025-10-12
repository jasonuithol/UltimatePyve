import pygame
import random
from controllers.move_controller import MoveController
from dark_libraries.dark_events import DarkEventService
from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.enums.direction_map import DIRECTION_MAP
from models.global_location import GlobalLocation

from models.location_metadata import LocationMetadata
from models.npc_agent import NpcAgent
from models.party_state import PartyState
from models.u5_map import U5Map

from services.combat_map_service import CombatMapService
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.main_loop_service import MainLoopService
from services.map_cache.map_cache_service import MapCacheService
from services.npc_service import NpcService

COMBAT_MAP_LOCATION_INDEX = -666

class CombatController(LoggerMixin):

    # Injectable
    party_state: PartyState
    npc_service: NpcService
    combat_map_service: CombatMapService
    global_registry: GlobalRegistry
    map_cache_service: MapCacheService
    console_service: ConsoleService
    
    # Idea #1
    main_loop_service: MainLoopService
    dark_event_service: DarkEventService
    display_service: DisplayService
    move_controller: MoveController

    def enter_combat(self, enemy_npc: NpcAgent):

        self.log(f"Entered combat with enemy_tile_id={enemy_npc.tile_id}")

        self.console_service.print_ascii(f"Entering combat with enemy_tile_id={enemy_npc.tile_id}")

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

        combat_spawn_location = GlobalLocation(-666, 0, Coord(5, 9))
        self.party_state.push_location(combat_spawn_location)

        # NPC freezing happens here.
        self.dark_event_service.pass_time(self.party_state.get_current_location())

        if enemy_npc.npc_metadata.max_party_size <= 1:
            monster_party_size = 1
        else:
            monster_party_size = random.randint(1, enemy_npc.npc_metadata.max_party_size)

        for monster_spawn_slot_index in range(monster_party_size):
            spawn_coord = combat_map._monster_spawn_coords[monster_spawn_slot_index]
            self.npc_service.add_npc(enemy_npc.spawn_clone_at(spawn_coord))

        enemy_npc.global_location = GlobalLocation(-666,0,Coord(5,2))

        in_combat = True
        current_location = combat_spawn_location

        while in_combat:

            event = self.main_loop_service.get_next_event()
            if event.type == pygame.QUIT:
                self.console_service.print_ascii("Cannot quit during combat !")
                continue

            if event.key == pygame.K_SPACE:
                self.log("DEBUG: Wait command received")
                self.dark_event_service.pass_time(current_location)
                continue

            move_offset = DIRECTION_MAP.get(event.key, None)
            if move_offset:
                move_outcome = self.move_controller.move(
                    current_location, 
                    move_offset, 
                    'walk'
                )
                if move_outcome.exit_map:
                    in_combat = False
                    break

                elif move_outcome.success:
                    self.log(f"DEBUG: Combat move received: {move_offset}")
                    current_location = current_location + move_offset
                    self.party_state.change_coord(current_location.coord)
                    self.dark_event_service.pass_time(current_location)

                else:
                    self.log(f"DEBUG: Combat move command failed: {move_outcome}")
            else:
                self.log(f"DEBUG: Received non-processable event: {event.key}")    

            self.display_service.render()


        self.party_state.pop_location()
        # NPC unfreezing happens here.
        self.dark_event_service.pass_time(self.party_state.get_current_location())

        self.npc_service.set_attacking_npc(None)
        self.npc_service.remove_npc(enemy_npc)
        self.log("Combat Over !")

        self.log(f"Exiting combat with enemy_tile_id={enemy_npc.tile_id}")




    