from datetime import timedelta

import pygame

from controllers.active_member_controller import ActiveMemberController
from controllers.cast_controller import CastController
from controllers.combat_controller import CombatController
from controllers.move_controller import MoveController, MoveOutcome
from controllers.ready_controller import ReadyController
from dark_libraries.dark_events import DarkEventListenerMixin, DarkEventService
from dark_libraries.dark_math   import Vector2
from dark_libraries.logging     import LoggerMixin

from data.global_registry     import GlobalRegistry

from models.enums.direction_map import DIRECTION_MAP, DIRECTION_NAMES
from models.global_location     import GlobalLocation
from models.interactable        import Interactable
from models.u5_map              import U5Map
from models.enums.inventory_offset import InventoryOffset

# singletons
from models.agents.party_agent import PartyAgent

from services.display_service import DisplayService
from services.input_service import InputService
from services.console_service import ConsoleService
from services.npc_service import NpcService
from services.view_port_service import ViewPortService
from services.world_clock import WorldClock

PASS_TIME      = True
DONT_PASS_TIME = False

class PartyController(DarkEventListenerMixin, LoggerMixin):

    # Injectable
    party_agent:        PartyAgent
    global_registry:    GlobalRegistry

    dark_event_service: DarkEventService
    main_loop_service:  InputService
    console_service:    ConsoleService
    npc_service:        NpcService
    world_clock:        WorldClock
    display_service:    DisplayService

    combat_controller:  CombatController
    move_controller:    MoveController
    active_member_controller: ActiveMemberController
    ready_controller: ReadyController
    cast_controller: CastController

    view_port_service: ViewPortService
    
    def run(self):

        self.npc_service.add_npc(self.party_agent)

        # Propogate the 'loaded' event to listeners.
        self.dark_event_service.loaded(self.party_agent.get_current_location())

        self._set_window_title()
        self.view_port_service.set_party_mode()

        while not self._has_quit:

            should_pass_time = self.dispatch_input()
            
            if should_pass_time:

                self.party_agent.spend_action_quanta()

                # Propgate pass_time event (and subsequently all other party-turn-based events.)
                self.dark_event_service.pass_time(self.party_agent.get_current_location())

                # Internal pass_time (e.g. torches going out)
                self.pass_time_internal()

                enemy_npc = self.npc_service.get_attacking_npc()
                
                if not enemy_npc is None:
                    #
                    # C O M B A T
                    #
                    self.combat_controller.enter_combat(enemy_npc)

    def dispatch_input(self) -> bool:
        
        event = self.main_loop_service.get_next_event()

        self.active_member_controller.handle_event(event)
        self.ready_controller.handle_event(event)
        self.cast_controller.handle_event(event, spell_caster = self.party_agent.get_active_member(), combat_map = None)

        #
        # Received key input, call appropriate handler.
        #
        direction_vector = DIRECTION_MAP.get(event.key, None)
        if not direction_vector is None:
            self.move(direction_vector)
            self._set_window_title()
            return PASS_TIME

        elif event.key == pygame.K_SPACE:
            self.console_service.print_ascii("Wait")
            return PASS_TIME

        elif event.key == pygame.K_j:
            self.console_service.print_ascii("Jimmy - ",include_carriage_return=False)
            action_direction = self.main_loop_service.obtain_action_direction()
            if not action_direction is None:
                self.jimmy(action_direction)
                return PASS_TIME

        elif event.key == pygame.K_i:
            self.ignite_torch()
            return PASS_TIME

        elif event.key == pygame.K_a:
            self.console_service.print_ascii("Attack - ",include_carriage_return=False)
            action_direction = self.main_loop_service.obtain_action_direction()
            if not action_direction is None:
                self.attack(action_direction)
                return PASS_TIME

        #
        # NOTE: For development and testing only
        #
        elif event.key == pygame.K_TAB:
            self.switch_outer_map()

        elif event.key == pygame.K_BACKQUOTE:
            self.rotate_transport()

        return DONT_PASS_TIME

    def _say_blocked(self):
        self.console_service.print_ascii("Blocked !")

    # good for loading a SAVE.GAM location that's in a town or dungeon or something, and you need to eventually 
    # resolve the overworld position when exiting.
    def load_location(self, location: GlobalLocation):

        self.party_agent.clear_locations()

        if location.location_index == 0:
            self.party_agent.push_location(location)

            self.log(f"Set party location to outer={location}")
        else:

            # Get outer world coords for starting position
            # will need this trick when importing saved games from OG U5 files.
            outer_location: GlobalLocation = None
            for entry_location, exit_location in self.global_registry.entry_triggers.items():
                if exit_location.location_index == location.location_index:
                    outer_location = entry_location

            assert not outer_location is None, f"Could not load overworld location for inner_location={location}"

            self.party_agent.push_location(outer_location)
            self.party_agent.push_location(location)

            self.log(f"Set party location to outer={outer_location}, inner={location}")

    def load_transport_state(self, transport_mode: int, last_east_west: int, last_nesw_dir: int):
        self.party_agent.set_transport_state(
            transport_mode = transport_mode,
            last_east_west = last_east_west,
            last_nesw_dir = last_nesw_dir
        )

        self.log(
            f"Set party transport state to transport_mode={self.party_agent.transport_mode}" 
            + 
            f", last_east_west={self.party_agent.last_east_west}"
            +
            f", last_nesw_dir={self.party_agent.last_nesw_dir}"
        )

    def _update_transport_state(self, move_offset: Vector2[int]):
        if move_offset.x == 1:
            # east
            self.party_agent.last_east_west = 0
            self.party_agent.last_nesw_dir = 1
        elif move_offset.x == -1:
            # west
            self.party_agent.last_east_west = 1
            self.party_agent.last_nesw_dir = 3
        elif move_offset.y == 1:
            # south
            self.party_agent.last_nesw_dir = 2
        elif move_offset.y == -1:
            # north
            self.party_agent.last_nesw_dir = 0


    #
    # Party driven State transitions
    #
    def move(self, move_offset: Vector2[int]):
        party_location = self.party_agent.get_current_location()
        transport_mode_name = self.global_registry.transport_modes.get(self.party_agent.transport_mode)
        move_outcome: MoveOutcome = self.move_controller.move(party_location, move_offset, transport_mode_name)

        if move_outcome.exit_map:
            current_map = self.global_registry.maps.get(party_location.location_index)
            self.party_agent.pop_location()
            self.console_service.print_ascii(f"Exited {current_map.name.capitalize()}")
            return

        if move_outcome.blocked:
            self._say_blocked()
            return
        
        if move_outcome.success:
            self._update_transport_state(move_offset)
            self.party_agent.change_coord(party_location.coord + move_offset)
            self.console_service.print_ascii(DIRECTION_NAMES[move_offset])
            return

        if not move_outcome.enter_map is None:
            self.party_agent.push_location(move_outcome.enter_map)

            new_map: U5Map = self.global_registry.maps.get(move_outcome.enter_map.location_index)
            self.console_service.print_ascii(f"Entered {new_map.name.capitalize()}")
            return

        if move_outcome.move_up:
            self.party_agent.change_level(party_location.level_index + 1)
            self.console_service.print_ascii("Up !")
            return

        if move_outcome.move_down:
            self.party_agent.change_level(party_location.level_index - 1)
            self.console_service.print_ascii("Down !")
            return

    def jimmy(self, direction: Vector2[int]):
        target_coord = self.party_agent.get_current_location().coord.add(direction)
        interactable: Interactable = self.global_registry.interactables.get(target_coord)      
        if interactable:
            interactable.jimmy()

    def ignite_torch(self):
        TORCH_RADIUS = 3
        TORCH_DURATION_HOURS = 4
        torch_count = self.global_registry.saved_game.read_u8(InventoryOffset.TORCHES)
        if torch_count == 0:
            self.console_service.print_ascii("No torches !")
            return
        self.console_service.print_ascii("Ignite torch !")
        self.global_registry.saved_game.write_u8(InventoryOffset.TORCHES, torch_count - 1)
        self.party_agent.set_light(TORCH_RADIUS, self.world_clock.get_natural_time() + timedelta(hours = TORCH_DURATION_HOURS))

    def attack(self, direction: Vector2[int]):
        target_coord = self.party_agent.get_current_location().coord.add(direction)
        enemy_party = self.npc_service.get_npc_at(target_coord)
        if enemy_party is None:
            return
        self.combat_controller.enter_combat(enemy_party)

    def pass_time_internal(self):

        # Internal
        if not self.party_agent.get_light_expiry() is None and self.world_clock.get_natural_time() > self.party_agent.get_light_expiry():
            self.party_agent.set_light(None, None)

    #
    # Testing only
    #

    def switch_outer_map(self):
        current_location = self.party_agent.get_current_location()
        if current_location.location_index != 0:
            return
        if current_location.level_index == 0:        
            new_level_index = 255 # underworld
        else:
            new_level_index = 0   # britannia
        self.party_agent.change_level(new_level_index)

    def rotate_transport(self):
        transport_mode = (self.party_agent.transport_mode + 1) % len(self.global_registry.transport_modes)
        self.party_agent.set_transport_state(transport_mode, self.party_agent.last_east_west, self.party_agent.last_nesw_dir)

    def _set_window_title(self):
        party_location = self.party_agent.get_current_location()
        active_map: U5Map = self.global_registry.maps.get(party_location.location_index)

        # Update window title with current location/world of player.
        self.display_service.set_window_title(
            f"{active_map.name} [{party_location.coord}]" 
            +
            f" time={self.world_clock.get_daylight_savings_time()}"
        )


