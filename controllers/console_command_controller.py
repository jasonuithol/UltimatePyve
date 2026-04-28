import pygame

from dark_libraries.logging import LoggerMixin

from services.console_command_service import ConsoleCommandService
from services.console_service         import ConsoleService
from services.input_service           import keycode_to_char


class ConsoleCommandController(LoggerMixin):

    # Injectable
    console_service:         ConsoleService
    console_command_service: ConsoleCommandService

    def __init__(self):
        super().__init__()
        self._active: bool = False
        self._buffer: str  = ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_BACKQUOTE:
            if self._active:
                self._deactivate(cancelled=True)
            else:
                self._activate()
            return True

        if not self._active:
            return False

        if event.key == pygame.K_RETURN:
            line = self._buffer
            self._buffer = ""
            self._active = False
            self.console_service.print_ascii("")  # newline after the typed command
            self.console_command_service.execute(line)
            return True

        if event.key == pygame.K_ESCAPE:
            self._deactivate(cancelled=True)
            return True

        if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            if self._buffer:
                self._buffer = self._buffer[:-1]
                self.console_service.backspace()
            return True

        char = keycode_to_char(event.key)
        if char is None or char in ("\n", "\t"):
            return True

        self._buffer += char
        self.console_service.print_ascii(char, include_carriage_return=False, no_prompt=True)
        return True

    def _activate(self):
        self._active = True
        self._buffer = ""
        self.console_service.print_ascii("> ", include_carriage_return=False)

    def _deactivate(self, cancelled: bool):
        self._active = False
        self._buffer = ""
        if cancelled:
            self.console_service.print_ascii(" [cancel]")
