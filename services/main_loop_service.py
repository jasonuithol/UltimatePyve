import pygame

from dark_libraries.dark_math import Coord, Rect, Vector2
from dark_libraries.logging   import LoggerMixin
from data.global_registry     import GlobalRegistry

from models.enums.cursor_type   import CursorType
from models.enums.direction_map import DIRECTION_MAP, DIRECTION_NAMES
from models.agents.party_agent  import PartyAgent

from services.console_service import ConsoleService
from services.display_service import DisplayService
from view.info_panel import InfoPanel

BIBLICALLY_ACCURATE_RANGE_TWEAK = 0.5

class MainLoopService(LoggerMixin):

    party_agent:     PartyAgent
    display_service: DisplayService
    console_service: ConsoleService
    global_registry: GlobalRegistry
    info_panel:      InfoPanel

    def __init__(self):
        super().__init__()
        self._is_running = True

    def _check_quit(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            # Clicking on the X will break out of the loop and exit the game.
            self._is_running = False
            return True
        return False

    def should_quit_game(self) -> bool:
        return self._is_running == False
    
    def choose_item(self, item_count: int) -> int:

        selected_item_index = 0
        self.info_panel.set_highlighted_item(selected_item_index)

        while self._is_running:

            event = self.get_next_event()

            if event.key == pygame.K_UP:
                selected_item_index = (selected_item_index - 1) % item_count

            elif event.key == pygame.K_DOWN:
                selected_item_index = (selected_item_index + 1) % item_count

            elif event.key == pygame.K_RETURN:
                # Pressing enter will return the chosen item index.
                self.info_panel.set_highlighted_item(None)
                return selected_item_index

            elif event.key == pygame.K_ESCAPE:
                # pressing escape will cancel the action
                self.info_panel.set_highlighted_item(None)
                return None

            else:
                # Nothing interesting happened.
                continue

            # Update the highlighted item
            self.info_panel.set_highlighted_item(selected_item_index)
    

    def obtain_action_direction(self) -> Vector2:

        self.console_service.print_ascii("Direction ? ", include_carriage_return = False)

        while self._is_running:

            event = self.get_next_event()

            if event.key == pygame.K_ESCAPE:
                # Pressing escape will just cancel the action.
                return None

            direction: Vector2 = DIRECTION_MAP.get(event.key, None)

            if not direction is None:
                self.console_service.print_ascii(DIRECTION_NAMES[direction] + " !")
                return direction

            
    def obtain_cursor_position(self, starting_coord: Coord, boundary_rect: Rect, range_: int) -> Coord:

        assert not starting_coord is None, "starting_coord cannot be None"
        assert range_ > 0, "range_ cannot be zero"

        self.console_service.print_ascii("Aim !")
        cursor = starting_coord

        crosshair_cursor_sprite = self.global_registry.cursors.get(CursorType.CROSSHAIR.value)
        self.display_service.set_cursor(CursorType.CROSSHAIR.value, cursor, crosshair_cursor_sprite)

        is_aiming = True
        while self._is_running and is_aiming:

            event = self.get_next_event()

            if event.key == pygame.K_ESCAPE:
                # Pressing escape will just cancel the action.
                is_aiming = False
                cursor = None

            elif event.key == pygame.K_RETURN or event.key == pygame.K_a:
                # Pressing enter or A will return the current cursor position.
                is_aiming = False

            else:
                direction: Vector2 = DIRECTION_MAP.get(event.key, None)

                if direction is None:
                    continue

                # Move the cursor
                target = cursor + direction
                if boundary_rect.is_in_bounds(target) and starting_coord.pythagorean_distance(target) <= range_ + BIBLICALLY_ACCURATE_RANGE_TWEAK:
                    cursor = target
                    self.display_service.set_cursor(CursorType.CROSSHAIR.value, cursor, crosshair_cursor_sprite)

        # We're done
        self.display_service.remove_cursor(CursorType.CROSSHAIR.value)
        return cursor
            
    def get_next_event(self) -> pygame.event.Event:

        while self._is_running:

            # NOTE: Technically this might skip events.  We can live with that for now.
            for event in pygame.event.get():

                if self._check_quit(event): 
                    return event

                elif event.type != pygame.KEYDOWN:
                    continue

                return event

            #
            # Waiting for input ? Render frames, ensuring that animations happen etc.
            #  
            self.display_service.render()
        
        # Failsafe - exiting this loop to get here means quitting the game.
        self.log("Exiting the get_next_event loop - switching to Quit Game mode.")
        self._is_running = False
        return pygame.event.Event(pygame.QUIT)
