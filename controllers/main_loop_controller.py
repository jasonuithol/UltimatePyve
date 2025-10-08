# file: main.py
import pygame
import gc

from controllers.display_controller  import DisplayController
from controllers.initialisation_controller import InitialisationController
from controllers.party_controller    import PartyController
from dark_libraries.service_provider import ServiceProvider
from dark_libraries.dark_math        import Vector2

from data.global_registry import GlobalRegistry

from models.party_state       import PartyState

from services.avatar_sprite_factory import AvatarSpriteFactory
from services.console_service import ConsoleService
from services.npc_service import NpcService
from services.world_clock     import WorldClock
from services.monster_spawner import MonsterSpawner

import service_composition
from view.main_display import MainDisplay
from view.view_port import ViewPort

def get_direction(event: pygame.event.Event) -> Vector2:
    if event.key == pygame.K_LEFT:
        return Vector2(-1, 0)
    elif event.key == pygame.K_RIGHT:
        return Vector2(+1, 0)
    elif event.key == pygame.K_UP:
        return Vector2(0, -1)
    elif event.key == pygame.K_DOWN:
        return Vector2(0, +1)
    return None

class MainLoopController:

    # Injectable
    global_registry: GlobalRegistry
    party_state: PartyState

    party_controller:    PartyController
    display_controller: DisplayController

    avatar_sprite_factory: AvatarSpriteFactory
    console_service:       ConsoleService
    monster_spawner:       MonsterSpawner
    world_clock:           WorldClock
    npc_service:           NpcService

    def update(self):
        # Player sprite
        transport_mode, direction = self.party_state.get_transport_state()
        player_sprite = self.avatar_sprite_factory.create_player(transport_mode, direction)
        self.display_controller.set_avatar_sprite(player_sprite)

        # update display
        party_location = self.party_state.get_current_location()
        self.display_controller.render(party_location.coord)

    def obtain_action_direction(self) -> Vector2:

        self.console_service.print_ascii("Direction ?")

        in_loop = True
        while in_loop:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    in_loop = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        in_loop = False
                    else:
                        direction = get_direction(event)
                        if not direction is None:
                            return direction

            #
            # all events processed.
            #  
            self.update()

        return None
    
    def process_event(self, event: pygame.event.Event):

        if event.key == pygame.K_TAB:
            self.party_controller.switch_outer_map()
            return

        if event.key == pygame.K_BACKQUOTE:
            self.party_controller.rotate_transport()
            return
         
        move_direction = get_direction(event)
        if not move_direction is None:
            self.party_controller.move(move_direction)
            return 

        if event.key == pygame.K_j:
            direction = self.obtain_action_direction()
            if direction:
                self.party_controller.jimmy(direction)
                return
            
        if event.key == pygame.K_i:
            self.party_controller.ignite_torch()
            return

        # Nothing changed
    
    def pass_time(self):
        #
        # TODO: Create a registry or event dispatcher for this
        #
        self.world_clock.pass_time()
#                    self.interactable_factory_registry.pass_time()
        self.party_controller.pass_time()
        self.monster_spawner.pass_time()
        self.npc_service.pass_time()

    def run(self):

        self.console_service.print_ascii([i for i in range(128)])
        self.console_service.print_runes([i for i in range(128)])

        running = True
        while running:
            for event in pygame.event.get():

                # Should only process KEYDOWN events as being "actions" that pass time.
                player_input_received = False

                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        player_input_received = True
                        self.process_event(event)

                # Allow "in=game" time to pass
                if player_input_received:
                    self.pass_time()

            #
            # all events processed.
            #  
            self.update()

        pygame.quit()

