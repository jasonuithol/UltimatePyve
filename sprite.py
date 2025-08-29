from typing import List, Callable
from loaders.tileset import load_tiles16_raw, TILES16_PATH
from dark_math import Coord

DEFAULT_FRAME_TIME_SECONDS = 0.5

class Sprite:
    def __init__(self, frames: List[List[List[int]]], transport_mode: str, frame_time: float = DEFAULT_FRAME_TIME_SECONDS):
        """
        frames: list of raw tile pixel arrays (palette indices), not Surfaces
        """
        self.frames = frames
        self.frame_time = frame_time
        self.current_frame = 0
        self.time_accum = 0.0
        self.world_coord = Coord(0,0)
        self.transport_mode = transport_mode

    def set_position(self, coord: Coord):
        self.world_coord = coord

    def move(self, dx: int, dy: int):
        self.world_coord
        self.world_x += dx
        self.world_y += dy

    def update(self, dt_seconds: float):
        self.time_accum += dt_seconds
        while self.time_accum >= self.frame_time:
            self.time_accum -= self.frame_time
            self.current_frame = (self.current_frame + 1) % len(self.frames)

    def get_current_frame_pixels(self) -> List[List[int]]:
        """Return the raw pixel array for the current frame."""
        return self.frames[self.current_frame]


# --- Factory function for the Avatar ---
def create_player(frame_time=DEFAULT_FRAME_TIME_SECONDS):
    PLAYER_FIRST_TILE = 332
    PLAYER_FRAME_COUNT = 4
    tileset_raw = load_tiles16_raw(TILES16_PATH)
    frames = tileset_raw[PLAYER_FIRST_TILE:PLAYER_FIRST_TILE + PLAYER_FRAME_COUNT]
    return Sprite(frames, 'walk', frame_time)

