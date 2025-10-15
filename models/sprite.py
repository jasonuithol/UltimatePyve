# file: animation/sprite.py
import math
import pygame
import random

from dark_libraries.logging import LoggerMixin
from models.tile import Tile

DEFAULT_FRAME_DURATION_SECONDS: float = 0.5

class Sprite(LoggerMixin):

    def __init__(self, frames: list[Tile] | None = None, frame_duration_seconds: float = DEFAULT_FRAME_DURATION_SECONDS):
        super().__init__()
        self.frames = [] if frames is None else frames
        self.set_frame_duration(frame_duration_seconds)
        self.log(f"DEBUG: Created sprite with {len(frames)} frames.")

    @classmethod
    def _seconds_since_init(cls) -> float:
        return pygame.time.get_ticks() / 1000

    def _get_current_frame_index(self) -> int:
        total_seconds_elapsed: float = __class__._seconds_since_init() + self.frame_offset_seconds
        num_frames_elapsed: int      = math.floor(total_seconds_elapsed / self.frame_duration_seconds)

        return num_frames_elapsed % len(self.frames)

    #
    # PUBLIC METHODS
    #

    def set_frame_duration(self, frame_duration_seconds: float):
        self.frame_duration_seconds = frame_duration_seconds
        self.frame_offset_seconds   = random.uniform(0.0, 1.0)  # TODO: This feature STILL doesn't work.

    def get_current_frame_tile(self) -> Tile:
        frame_index = self._get_current_frame_index()
        return self.frames[frame_index]







