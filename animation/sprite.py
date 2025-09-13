# file: animation/sprite.py
from typing import List, Optional
from tileset import Tile

class Sprite:
    def __init__(self, frames: Optional[List[Tile]] = None, frame_time: float = 0.5, frame_time_offset: float = 0.0):
        """
        frames: list of raw tile pixel arrays (palette indices), not Surfaces
        """
        self.frames = [] if frames is None else frames

        self.frame_time = frame_time                # in seconds
        self.frame_time_offset = frame_time_offset  # in seconds - btw this feature STILL doesn't work.

    def set_frame_time(self, frame_time: float, frame_time_offset: float):
        self.frame_time = frame_time
        self.frame_time_offset = frame_time_offset

    def get_current_frame_index(self, ticks_since_init: int) -> int:
        total_seconds_elapsed: float = (ticks_since_init / 1000) + self.frame_time_offset
        num_frames_elapsed: int = int(total_seconds_elapsed // self.frame_time)
        return num_frames_elapsed % len(self.frames)

    def get_current_frame_tile(self, ticks_since_init: int) -> Tile:
        frame_index = self.get_current_frame_index(ticks_since_init)
        return self.frames[frame_index]







