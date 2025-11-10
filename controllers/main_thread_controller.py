import time
import pygame.event

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.logging import LoggerMixin

from services.display_service import DisplayService
from services.input_service import InputService
from services.sound_service import SoundService

# =============================================================
#
# pygame uses SDL, which only likes talking to the main thread.
#            (SDL = Simple DirectMedia Layer)
#
# =============================================================

class MainThreadController(LoggerMixin, DarkEventListenerMixin):

    # All of these use SDL, or process SDL objects.
    display_service: DisplayService    # pygame.draw/image/transform
    input_service:   InputService      # pygame.event
    sound_service:   SoundService      # pygame.mixer

    def enter_main_loop(self):
        self.is_alive = True

        while self.is_alive:

            self.display_service.render()

            self.sound_service.render()
            
            events = [e for e in pygame.event.get() if e.type in [pygame.QUIT, pygame.KEYDOWN]]
            if any(events):
                self.input_service.inject_events(events)

            time.sleep(0.001)

        self.log("Exiting")

    def stop(self):
        self.is_alive = False


