import queue
from typing import Iterable
import pygame
import time

from dark_libraries.dark_events import DarkEventListenerMixin, DarkEventService
from dark_libraries.dark_math import Coord, Rect, Vector2
from dark_libraries.logging   import LoggerMixin
from data.global_registry     import GlobalRegistry

from models.enums.cursor_type   import CursorType
from models.enums.direction_map import DIRECTION_MAP, DIRECTION_NAMES

from services.console_service import ConsoleService
from services.display_service import DisplayService

from services.multiplayer_service import MultiplayerService
from services.view_port_service import ViewPortService

BIBLICALLY_ACCURATE_RANGE_TWEAK = 0.5

class SyntheticQuit:
    def __init__(self):
        self.key = -1
        self.type = -1
        self.mod = 0

class EmptyEvent:
    def __init__(self):
        self.key = -1
        self.type = -1
        self.mod = 0

class InputServiceImplementation(DarkEventListenerMixin, LoggerMixin):

    display_service: DisplayService
    console_service: ConsoleService
    global_registry: GlobalRegistry
    dark_event_service: DarkEventService
    view_port_service:  ViewPortService
    multiplayer_service: MultiplayerService

    def __init__(self):
        super().__init__()

        # An object designed to prevent event handlers blowing up
        self._fake_quit_event = SyntheticQuit()        

        self._event_queue = queue.Queue(100)

    def _check_quit(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.dark_event_service.quit()
            return True
        elif event == self._fake_quit_event:
            return True
        return False

    def obtain_action_direction(self) -> Vector2[int]:

        self.console_service.print_ascii("Direction ? ", include_carriage_return = False)

        while not self._has_quit:

            event = self.get_next_event()

            if self._check_quit(event):
                # Quitting will cancel the action (and quit)
                return None           

            if event.key == pygame.K_ESCAPE:
                # Pressing escape will just cancel the action.
                return None

            direction: Vector2[int] = DIRECTION_MAP.get(event.key, None)

            if not direction is None:
                self.console_service.print_ascii(DIRECTION_NAMES[direction] + " !")
                return direction
            
            time.sleep(0.1)

        return None
            
    def obtain_cursor_position(self, starting_coord: Coord[int], boundary_rect: Rect[int], range_: int) -> Coord[int]:

        assert not starting_coord is None, "starting_coord cannot be None"
        assert range_ > 0, "range_ cannot be zero"

        self.console_service.print_ascii("Aim !")
        cursor = starting_coord

        crosshair_cursor_sprite = self.global_registry.cursors.get(CursorType.CROSSHAIR.value)
        self.view_port_service.set_cursor(CursorType.CROSSHAIR.value, cursor, crosshair_cursor_sprite)

        is_aiming = True
        while (not self._has_quit) and is_aiming:

            event = self.get_next_event()

            if self._check_quit(event):
                # Quitting will cancel the action (and quit)
                return None             

            if event.key == pygame.K_ESCAPE:
                # Pressing escape will just cancel the action.
                is_aiming = False
                cursor = None

            elif event.key == pygame.K_RETURN or event.key == pygame.K_a:
                # Pressing enter or A will return the current cursor position.
                is_aiming = False

            else:
                direction: Vector2[int] = DIRECTION_MAP.get(event.key, None)

                if not direction is None:

                    # Move the cursor
                    target = cursor + direction
                    if boundary_rect.is_in_bounds(target) and starting_coord.pythagorean_distance(target) <= range_ + BIBLICALLY_ACCURATE_RANGE_TWEAK:
                        cursor = target
                        self.view_port_service.set_cursor(CursorType.CROSSHAIR.value, cursor, crosshair_cursor_sprite)

            time.sleep(0.1)

        # We're done
        self.view_port_service.remove_cursor(CursorType.CROSSHAIR.value)
        return cursor
            
    def get_next_event(self) -> pygame.event.Event:

        try:
            event = self._event_queue.get_nowait()

            if self._check_quit(event):
                return self._fake_quit_event                

            return event
            
        except queue.Empty:
            pass

        return EmptyEvent()

    def discard_events(self):

        num = 0
        while not self._event_queue.empty():
            self._event_queue.get()
            num += 1
            time.sleep(0.001)

        if num > 0:
            self.log(f"DEBUG: Discarded {num} events")

    def inject_events(self, events: Iterable[pygame.event.Event]):

        self.log(f"DEBUG: Injecting {len(events)} events.")

        for event in events:
            try:
                self._event_queue.put_nowait(event)
            except queue.Full:
                self.log(f"ERROR: Input queue full, dropping event: {event}")
