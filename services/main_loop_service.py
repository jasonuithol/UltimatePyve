import pygame

from dark_libraries.dark_math import Coord, Rect, Vector2
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.enums.cursor_type import CursorType
from models.enums.direction_map import DIRECTION_MAP, DIRECTION_NAMES
from models.agents.party_agent import PartyAgent

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
    pygame.K_a
]

class MainLoopService(LoggerMixin):

    party_agent:     PartyAgent
    display_service: DisplayService
    console_service: ConsoleService
    global_registry: GlobalRegistry

    def _after_inject(self):
        self._is_running = True

    def should_quit_game(self) -> bool:
        return self._is_running == False

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
            
    def obtain_cursor_position(self, starting_coord: Coord, boundary_rect: Rect) -> Coord:

        assert not starting_coord is None, "starting_coord cannot be None"

        self.console_service.print_ascii("Where ? ")
        cursor = starting_coord

        crosshair_cursor_sprite = self.global_registry.cursors.get(CursorType.CROSSHAIR.value)
        self.display_service.set_cursor(CursorType.CROSSHAIR.value, cursor, crosshair_cursor_sprite)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Clicking on the X will break out of the loop and exit the game.
                    self.display_service.remove_cursor(CursorType.CROSSHAIR.value)
                    self._is_running = False
                    return None

                if event.type != pygame.KEYDOWN:
                    continue

                if event.key == pygame.K_ESCAPE:
                    # Pressing escape will just cancel the action.
                    self.display_service.remove_cursor(CursorType.CROSSHAIR.value)
                    return None

                if event.key == pygame.K_RETURN:
                    # Pressing enter will return the current cursor position.
                    self.display_service.remove_cursor(CursorType.CROSSHAIR.value)
                    return cursor

                direction: Vector2 = DIRECTION_MAP.get(event.key, None)
                if not direction is None:
                    target = cursor + direction
                    if boundary_rect.is_in_bounds(target):
                        cursor = target
                        self.display_service.set_cursor(CursorType.CROSSHAIR.value, cursor, crosshair_cursor_sprite)
                        self.log(f"DEBUG: Moved attack cursor to {target}")

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
