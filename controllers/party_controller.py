from datetime import timedelta
from typing   import Iterable

import pygame

from controllers.combat_controller import CombatController
from dark_libraries.dark_events import DarkEventService
from dark_libraries.dark_math   import Coord, Vector2
from dark_libraries.logging     import LoggerMixin

from data.global_registry     import GlobalRegistry

from models.enums.direction_map import DIRECTION_MAP, DIRECTION_NAMES
from models.global_location     import GlobalLocation
from models.interactable        import Interactable
from models.move_into_result    import MoveIntoResult
from models.terrain             import Terrain
from models.u5_map              import U5Map
from models.enums.inventory_offset  import InventoryOffset

# singletons
from models.party_inventory   import PartyInventory
from models.party_state       import PartyState

from services.main_loop_service import MainLoopService
from services.console_service import ConsoleService
from services.npc_service import NpcService
from services.world_clock import WorldClock

#from .saved_game import SavedGame

PASS_TIME      = True
DONT_PASS_TIME = False

class PartyController(LoggerMixin):

    # Injectable
    party_state:     PartyState
    global_registry: GlobalRegistry
    party_inventory: PartyInventory

    dark_event_service:    DarkEventService
    main_loop_service:     MainLoopService
    console_service:       ConsoleService
    npc_service:           NpcService
    world_clock:           WorldClock

    combat_controller:     CombatController

    '''
    sound_track_player:    SoundTrackPlayer
    avatar_sprite_factory: AvatarSpriteFactory
    door_instance_factory: DoorInstanceFactory
    monster_spawner:       MonsterSpawner
    display_service:       DisplayService
    '''

    def _after_inject(self):
        self._is_running = True

    def run(self):

        # Propogate the 'loaded' event to listeners.
        self.dark_event_service.loaded(self.party_state.get_current_location())

        while self._is_running:
            should_pass_time = self.dispatch_input()
            
            if should_pass_time:
                # Propgate pass_time event (and subsequently all other party-turn-based events.)
                self.dark_event_service.pass_time(self.party_state.get_current_location())

                # Internal pass_time (e.g. torches going out)
                self.pass_time()

                enemy_npc = self.npc_service.get_attacking_npc()
                if not enemy_npc is None:
                    self.combat_controller.enter_combat(enemy_npc)

                

    def dispatch_input(self) -> bool:
        
        event = self.main_loop_service.get_next_event()

        if event.type == pygame.QUIT:
            self._is_running = False
            return DONT_PASS_TIME

        if event.type != pygame.KEYDOWN:
            return DONT_PASS_TIME

        #
        # Received key input, call appropriate handler.
        #
        direction_vector = DIRECTION_MAP.get(event.key, None)
        if not direction_vector is None:
            self.move(direction_vector)
            return PASS_TIME

        elif event.key == pygame.K_SPACE:
            self.console_service.print_ascii("Wait")
            return PASS_TIME

        elif event.key == pygame.K_j:
            action_direction = self.main_loop_service.obtain_action_direction()
            if not action_direction is None:
                self.jimmy(action_direction)
                return PASS_TIME

        elif event.key == pygame.K_i:
            self.ignite_torch()
            return PASS_TIME

        #
        # NOTE: For development and testing only
        #
        elif event.key == pygame.K_TAB:
            self.switch_outer_map()

        elif event.key == pygame.K_BACKQUOTE:
            self.switch_outer_map()

        return DONT_PASS_TIME

    def _say_blocked(self):
        self.console_service.print_ascii("Blocked !")

    # good for loading a SAVE.GAM location that's in a town or dungeon or something, and you need to eventually 
    # resolve the overworld position when exiting.
    def load_inner_location(self, inner_location: GlobalLocation):

        # Get outer world coords for starting position
        # will need this trick when importing saved games from OG U5 files.
        outer_location: GlobalLocation = None
        for entry_location, exit_location in self.global_registry.entry_triggers.items():
            if exit_location.location_index == inner_location.location_index:
                outer_location = entry_location
        
        assert not outer_location is None, f"Could not load overworld location for {inner_location}"

        self.party_state.clear_locations()
        self.party_state.push_location(outer_location)
        self.party_state.push_location(inner_location)

        self.log(f"Set party location to outer={outer_location}, inner={inner_location}")

    def load_transport_state(self, transport_mode: int, last_east_west: int, last_nesw_dir: int):
        self.party_state.set_transport_state(
            transport_mode = transport_mode,
            last_east_west = last_east_west,
            last_nesw_dir = last_nesw_dir
        )

        self.log(
            f"Set party transport state to transport_mode={self.party_state.transport_mode}" 
            + 
            f", last_east_west={self.party_state.last_east_west}"
            +
            f", last_nesw_dir={self.party_state.last_nesw_dir}"
        )

    def load_party_inventory(self, inventory: Iterable[tuple[InventoryOffset, int]]):
        for inventory_offset, additional_quantity in inventory:
            self.party_inventory.add(inventory_offset, additional_quantity)

    # TODO: Choose a better name for this method
    def _can_traverse(self, target: Coord) -> MoveIntoResult:

        transport_mode     = self.global_registry.transport_modes.get(self.party_state.transport_mode)
        current_location   = self.party_state.get_current_location()
        current_map: U5Map = self.global_registry.maps.get(current_location.location_index)
        target_tile_id     = current_map.get_tile_id(current_location.level_index, target)

        interactable: Interactable = self.global_registry.interactables.get(target)      

        if interactable:
            interactable_moveinto_result = interactable.move_into()
            if interactable_moveinto_result.traversal_allowed == False and interactable_moveinto_result.alternative_action_taken == False:
                self._say_blocked()
            return interactable_moveinto_result

        # It's just regular terrain.
        terrain: Terrain = self.global_registry.terrains.get(target_tile_id)
        can_traverse_base_terrain = terrain.can_traverse(transport_mode)

        if not can_traverse_base_terrain:
            self._say_blocked()

        return MoveIntoResult(
            traversal_allowed = can_traverse_base_terrain,
            alternative_action_taken = False
        )


    #
    # Player driven State transitions
    #

    def move(self, move_offset: Vector2):

        current_location = self.party_state.get_current_location()
        current_map: U5Map = self.global_registry.maps.get(current_location.location_index)
        target_location = current_location + move_offset

        # Handle out-of-bounds.
        if current_map.location_index == 0:
            # When in the overworld/underworld, wrap the coord because it's a globe.
            target_location = target_location.move_to_coord(current_map.get_wrapped_coord(target_location.coord))
        else:
            # When in a town/dungeon room/combat map etc, going out-of-bounds means exiting the map
            if not current_map.get_size().is_in_bounds(target_location.coord):
                self.party_state.pop_location()
                new_location = self.party_state.get_current_location()
                
                self.console_service.print_ascii(f"Exited {current_map.name.capitalize()}")
                return

        # Handle un-traversable terrain.
        if not self._can_traverse(target_location.coord).traversal_allowed:
            self._say_blocked()
            return

        # handle bumping into NPCs.
        if target_location.coord in self.npc_service.get_occupied_coords():
            self._say_blocked()
            return

        # Move
        self.party_state.change_coord(target_location.coord)
        self.console_service.print_ascii(DIRECTION_NAMES[move_offset])

        # map level change checks.
        target_tile_id = current_map.get_tile_id(current_location.level_index, target_location.coord)
        target_terrain: Terrain = self.global_registry.terrains.get(target_tile_id)
        new_level_index = current_location.level_index

        # entry points
        if target_terrain.entry_point == True:
            new_location: GlobalLocation = self.global_registry.entry_triggers.get(target_location)
            self.party_state.push_location(new_location)

            new_map: U5Map = self.global_registry.maps.get(new_location.location_index)
            self.console_service.print_ascii(f"Entered {new_map.name.capitalize()}")
            return

        # ladders                
        if target_terrain.move_up == True:
            new_level_index = target_location.level_index + 1

        if target_terrain.move_down == True:
            new_level_index = target_location.level_index - 1

        # stairs
        if target_terrain.stairs == True:
            # NOTE: This is just a guess, but seems to be working out ok.
            if current_location.level_index == current_map.default_level_index:
                new_level_index = current_map.default_level_index + 1
            else:
                new_level_index = current_map.default_level_index

        # update level if changed.
        if current_location.level_index != new_level_index:
            if new_level_index > current_location.level_index:
                self.console_service.print_ascii("Up !")
            else:
                self.console_service.print_ascii("Down !")
            self.party_state.change_level(new_level_index)

        # Transport direction, and console message.
        if move_offset.x == 1:
            # east
            self.party_state.last_east_west = 0
            self.party_state.last_nesw_dir = 1
        elif move_offset.x == -1:
            # west
            self.party_state.last_east_west = 1
            self.party_state.last_nesw_dir = 3
        elif move_offset.y == 1:
            # south
            self.party_state.last_nesw_dir = 2
        elif move_offset.y == -1:
            # north
            self.party_state.last_nesw_dir = 0
            

    def jimmy(self, direction: Vector2):

        target_coord = self.party_state.get_current_location().coord.add(direction)
        interactable: Interactable = self.global_registry.interactables.get(target_coord)      
        if interactable:
            interactable.jimmy()

    def ignite_torch(self):
        TORCH_RADIUS = 3
        TORCH_DURATION_HOURS = 4
        if self.party_inventory.get_quantity(InventoryOffset.TORCHES) == 0:
            self.console_service.print_ascii("No torches !")
            return
        self.console_service.print_ascii("Ignite torch !")
        self.party_inventory.add(InventoryOffset.TORCHES, -1)
        self.party_state.set_light(TORCH_RADIUS, self.world_clock.get_natural_time() + timedelta(hours = TORCH_DURATION_HOURS))

    def pass_time(self):

        # Internal
        if not self.party_state.get_light_expiry() is None and self.world_clock.get_natural_time() > self.party_state.get_light_expiry():
            self.party_state.set_light(None, None)

    #
    # Testing only
    #

    def switch_outer_map(self):
        current_location = self.party_state.get_current_location()
        if current_location.location_index != 0:
            return
        if current_location.level_index == 0:        
            current_location.level_index = 255 # underworld
        else:
            current_location.level_index = 0   # britannia

    def rotate_transport(self):
        self.party_state.transport_mode = (self.party_state.transport_mode + 1) % len(self.global_registry.transport_modes)
