# file: animation/sprite.py
import pygame

from models.tile import Tile

DEFAULT_FRAME_TIME = 0.5

class Sprite:
    def __init__(self, frames: list[Tile] | None = None, frame_time: float = DEFAULT_FRAME_TIME, frame_time_offset: float = 0.0):
        """
        frames: list of raw tile pixel arrays (palette indices), not Surfaces
        """
        self.frames = [] if frames is None else frames

        self.frame_time = frame_time                # in seconds
        self.frame_time_offset = frame_time_offset  # in seconds - btw this feature STILL doesn't work.

    @classmethod
    def _ticks_since_init(cls):
        return pygame.time.get_ticks()

    def set_frame_time(self, frame_time: float, frame_time_offset: float):
        self.frame_time = frame_time
        self.frame_time_offset = frame_time_offset

    def get_current_frame_index(self) -> int:
        total_seconds_elapsed: float = (__class__._ticks_since_init() / 1000) + self.frame_time_offset
        num_frames_elapsed: int = int(total_seconds_elapsed // self.frame_time)
        return num_frames_elapsed % len(self.frames)

    def get_current_frame_tile(self) -> Tile:
        frame_index = self.get_current_frame_index()
        return self.frames[frame_index]







