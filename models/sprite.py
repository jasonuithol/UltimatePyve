import pygame
import random

from dark_libraries.logging import LoggerMixin

DEFAULT_FRAME_DURATION_SECONDS: float = 0.5

class Sprite[TFrame](LoggerMixin):

    def __init__(self, frames: list[TFrame] | None = None, frame_duration_seconds: float = DEFAULT_FRAME_DURATION_SECONDS):
        super().__init__()
        self.frames = [] if frames is None else frames
        self.set_uniform_frame_duration(frame_duration_seconds)

    def _finalize_frame_durations(self):

        self.frame_cycle_duration = sum(self.frame_durations)
        self.frame_duration_ranges = list[tuple[float,float]]()
        frame_duration_accumulator: float = 0.00
        for frame_duration in self.frame_durations:
            frame_range = (
                frame_duration_accumulator, 
                frame_duration_accumulator + frame_duration
            )
            self.frame_duration_ranges.append(frame_range)
            frame_duration_accumulator += frame_duration

    @classmethod
    def _seconds_since_init(cls) -> float:
        return pygame.time.get_ticks() / 1000

    def _get_current_frame_index(self, time_offset_seconds) -> int:
        total_seconds_elapsed:          float = __class__._seconds_since_init() + time_offset_seconds
        seconds_since_last_cycle_start: float = total_seconds_elapsed % self.frame_cycle_duration

        for frame_index, frame_duration_range in enumerate(self.frame_duration_ranges):
            frame_start, frame_stop = frame_duration_range
            if frame_start <= seconds_since_last_cycle_start < frame_stop:
                return frame_index % len(self.frames)
            
        # A safety fallback.  Shouldn't really get here.
        return frame_index % len(self.frames)

    #
    # PUBLIC METHODS
    #

    def set_uniform_frame_duration(self, frame_duration_seconds: float):
        self.frame_durations = list[float]()
        for _ in self.frames:
            self.frame_durations.append(frame_duration_seconds)
        self._finalize_frame_durations()

    def set_randomized_frame_durations(self):
        for _ in self.frames:
            for _ in range(17): # some arbitrary, prime number
                self.frame_durations.append(random.uniform(0.0, 1.0))
        self._finalize_frame_durations()

    def create_random_time_offset(self) -> float:
        return random.uniform(0.0, self.frame_cycle_duration)

    def get_current_frame(self, time_offset_seconds: float) -> TFrame:
        frame_index = self._get_current_frame_index(time_offset_seconds)
        return self.frames[frame_index]







