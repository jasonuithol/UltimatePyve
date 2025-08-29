from typing import List
from loaders.tileset import load_tiles16_raw, TILES16_PATH
from dark_math import Coord
from terrain import get_transport_modes

DEFAULT_FRAME_TIME_SECONDS = 0.5

class Sprite:
    def __init__(self, frames: List[List[List[int]]], frame_time: float = DEFAULT_FRAME_TIME_SECONDS):
        """
        frames: list of raw tile pixel arrays (palette indices), not Surfaces
        """
        self.frames = frames
        self.frame_time = frame_time
        self.world_coord = Coord(0,0)

    def set_position(self, coord: Coord):
        self.world_coord = coord

    def get_current_frame_pixels(self, ticks_since_init: int) -> List[List[int]]:
        num_frames_elapsed: int = int((ticks_since_init / 1000) // self.frame_time)
        current_frame = num_frames_elapsed % len(self.frames)
        return self.frames[current_frame]


# --- Factory function for the Avatar sprites ---
def create_player(transport_mode: int, direction: int) -> Sprite:
    transport_name = get_transport_modes()[transport_mode]
    func = globals()[f"create_player_{transport_name}"]
    return func(direction)

def _create_player_any(PLAYER_FIRST_TILE:int, PLAYER_FRAME_COUNT:int, frame_time=DEFAULT_FRAME_TIME_SECONDS) -> Sprite:
    tileset_raw = load_tiles16_raw(TILES16_PATH)
    frames = tileset_raw[PLAYER_FIRST_TILE:PLAYER_FIRST_TILE + PLAYER_FRAME_COUNT]
    return Sprite(frames, frame_time)

def create_player_walk(_whatever: int) -> Sprite:
    return _create_player_any(332, 4)

def create_player_horse(direction: int) -> Sprite:
    return _create_player_any(274 + direction, 1)

def create_player_carpet(direction: int) -> Sprite:
    return _create_player_any(276 + direction, 1)

def create_player_skiff(direction: int) -> Sprite:
    return _create_player_any(296 + direction, 1)

def create_player_ship(direction: int) -> Sprite:
    return _create_player_any(292 + direction, 1)

def create_player_sail(direction: int) -> Sprite:
    return _create_player_any(288 + direction, 1)
