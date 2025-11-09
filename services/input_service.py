import pygame

from typing import Protocol
from dark_libraries.dark_math import Coord, Rect, Vector2

def keycode_to_char(keycode):
    # Letters and digits
    if pygame.K_a <= keycode <= pygame.K_z:
        return chr(keycode)
    elif pygame.K_0 <= keycode <= pygame.K_9:
        return chr(keycode)
    
    # Special keys
    special_map = {
        pygame.K_SPACE: ' ',
        pygame.K_COMMA: ',',
        pygame.K_PERIOD: '.',
        pygame.K_RETURN: '\n',
        pygame.K_TAB: '\t',
        pygame.K_MINUS: '-',
        pygame.K_EQUALS: '=',
        pygame.K_SLASH: '/',
        pygame.K_BACKSLASH: '\\',
        pygame.K_SEMICOLON: ';',
        pygame.K_QUOTE: "'",
        pygame.K_LEFTBRACKET: '[',
        pygame.K_RIGHTBRACKET: ']',
        pygame.K_BACKQUOTE: '`',
    }
    return special_map.get(keycode, None)

class InputService(Protocol):

    def obtain_action_direction(self) -> Vector2[int]: ...
    def obtain_cursor_position(self, starting_coord: Coord[int], boundary_rect: Rect[int], range_: int) -> Coord[int]: ...
    def get_next_event(self) -> pygame.event.Event: ...
    def discard_events(self): ...
#    def inject_event(self, event: pygame.event.Event): ...
