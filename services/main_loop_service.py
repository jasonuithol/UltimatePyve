import pygame

from dark_libraries.dark_math import Vector2
from dark_libraries.logging import LoggerMixin
from models.enums.direction_map import DIRECTION_MAP, DIRECTION_NAMES
from models.party_state import PartyState

from services.avatar_sprite_factory import AvatarSpriteFactory
from services.console_service import ConsoleService
from services.display_service import DisplayService


PROCESSABLE_KEYS = [

    # for testing only
    pygame.K_TAB,
    pygame.K_BACKQUOTE,

    # movement
    pygame.K_LEFT,
    pygame.K_RIGHT,
    pygame.K_UP,
    pygame.K_DOWN,

    # party/member actions
    pygame.K_SPACE, # pass time
    pygame.K_j, # jimmy
    pygame.K_i, # ignite torch
]

class MainLoopService(LoggerMixin):

    party_state: PartyState
    avatar_sprite_factory: AvatarSpriteFactory
    display_service: DisplayService
    console_service: ConsoleService

    def _after_inject(self):
        self._is_running = True

    '''
    def _update(self):
        # Player sprite
        transport_mode, direction = self.party_state.get_transport_state()
        player_sprite = self.avatar_sprite_factory.create_player(transport_mode, direction)
        self.display_service.set_avatar_sprite(player_sprite)

        # update display
        party_location = self.party_state.get_current_location()
        self.display_service.render(party_location.coord)
    '''

    def obtain_action_direction(self) -> Vector2:

        self.console_service.print_ascii("Direction ? ", include_carriage_return = False)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Clicking on the X will break out of the loop and exit the game.
                    self._is_running = False
                    return None

                if event.type != pygame.KEYDOWN:
                    continue

                if event.key == pygame.K_ESCAPE:
                    # Pressing escape will just cancel the action.
                    return None

                direction: Vector2 = DIRECTION_MAP.get(event.key, None)

                if not direction is None:
                    self.console_service.print_ascii(DIRECTION_NAMES[direction] + " !")
                    return direction

            #
            # Waiting for input ? Render frames, ensuring that animations happen etc.
            #  
            self.display_service.render()
            
    def get_next_event(self) -> pygame.event.Event:

        while self._is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return pygame.event.Event(pygame.QUIT)

                if event.type != pygame.KEYDOWN:
                    continue

                if event.key in PROCESSABLE_KEYS: 
                    return event

            #
            # Waiting for input ? Render frames, ensuring that animations happen etc.
            #  
            self.display_service.render()
        
        return pygame.event.Event(pygame.QUIT)
