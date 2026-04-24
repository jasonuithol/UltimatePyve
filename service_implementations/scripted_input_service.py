from collections import deque

import pygame

from service_implementations.input_service_implementation import InputServiceImplementation


class ScriptedInputService(InputServiceImplementation):
    """
    Test-mode InputService: returns KEYDOWN events from a pre-queued buffer
    instead of polling pygame. When the queue drains, fires a dark quit so
    party_controller.run() exits naturally.
    """

    def __init__(self):
        super().__init__()
        self._queued_events: deque[pygame.event.Event] = deque()

    def queue_key(self, key: int):
        self._queued_events.append(pygame.event.Event(pygame.KEYDOWN, key=key))

    def queue_keys(self, *keys: int):
        for key in keys:
            self.queue_key(key)

    def queue_string(self, text: str):
        # For console command typing: one char at a time, plus Enter.
        for ch in text:
            key = self._char_to_keycode(ch)
            if key is not None:
                self.queue_key(key)
        self.queue_key(pygame.K_RETURN)

    @staticmethod
    def _char_to_keycode(ch: str) -> int | None:
        if "a" <= ch <= "z":
            return ord(ch)
        if "A" <= ch <= "Z":
            return ord(ch.lower())
        if "0" <= ch <= "9":
            return ord(ch)
        return {
            " ":  pygame.K_SPACE,
            "'":  pygame.K_QUOTE,
            ",":  pygame.K_COMMA,
            ".":  pygame.K_PERIOD,
            "-":  pygame.K_MINUS,
            "`":  pygame.K_BACKQUOTE,
        }.get(ch)

    def get_next_event(self) -> pygame.event.Event:
        if self._has_quit:
            return self._fake_quit_event
        if self._queued_events:
            return self._queued_events.popleft()
        # Queue exhausted — quit gracefully so the outer loop exits.
        self.dark_event_service.quit()
        return self._fake_quit_event
