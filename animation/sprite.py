# file: animation/sprite.py
from copy import copy
from typing import Dict, List, Optional, Self

from dark_libraries.dark_math import Coord
from loaders.tileset import TileSet, Tile

class Sprite:
    def __init__(self, frames: Optional[List[Tile]] = None, frame_time: float = 0.5, frame_time_offset: float = 0.0):
        """
        frames: list of raw tile pixel arrays (palette indices), not Surfaces
        """
        self.frames = [] if frames is None else frames

        self.frame_time = frame_time                # in seconds
        self.frame_time_offset = frame_time_offset  # in seconds - btw this feature STILL doesn't work.
        self.world_coord = Coord(0,0)

    def set_position(self, coord: Coord):
        self.world_coord = coord

    def set_frame_time(self, frame_time: float, frame_time_offset: float):
        self.frame_time = frame_time
        self.frame_time_offset = frame_time_offset

    def get_current_frame_index(self, ticks_since_init: int) -> int:
        total_seconds_elapsed: float = (ticks_since_init / 1000) + self.frame_time_offset
        num_frames_elapsed: int = int(total_seconds_elapsed // self.frame_time)
        return num_frames_elapsed % len(self.frames)

    def get_current_frame_tile(self, ticks_since_init: int) -> Tile:
        return self.frames[self.get_current_frame_index(ticks_since_init)]

    def spawn_from_master(self, coord: Coord) -> Self:
        sprite_copy = copy(self)
        sprite_copy.world_coord = coord
        # TODO: Get time_offsets working...
        return sprite_copy

class AvatarSpriteFactory:

    # Injectable
    tileset: TileSet

    # --- Factory function for the Avatar sprites ---
    def create_player(self, transport_mode: int, direction: int) -> Sprite:
        transport_name = ["walk","horse","carpet","skiff","ship","sail"][transport_mode]
        func = getattr(self, f"create_player_{transport_name}")
        return func(direction)

    def _create_player_any(self, player_first_tile:int, player_frame_count:int) -> Sprite:
        frames = self.tileset.tiles[player_first_tile:player_first_tile + player_frame_count]
        return Sprite(frames)

    def create_player_walk(self,  _whatever: int) -> Sprite:
        return self._create_player_any(332, 4)

    def create_player_horse(self, direction: int) -> Sprite:
        return self._create_player_any(274 + direction, 1)

    def create_player_carpet(self, direction: int) -> Sprite:
        return self._create_player_any(276 + direction, 1)

    def create_player_skiff(self, direction: int) -> Sprite:
        return self._create_player_any(296 + direction, 1)

    def create_player_ship(self, direction: int) -> Sprite:
        return self._create_player_any(292 + direction, 1)

    def create_player_sail(self, direction: int) -> Sprite:
        return self._create_player_any(288 + direction, 1)



class AnimatedTileFactory:

    # Injectable
    tileset: TileSet

    # (start tile, num frames)
    animated_tiles = [
        (128,2),    # axe table
        (130,2),    # axe table 2
        (212,4),    # waterfall
        (216,4),    # fountain
        (232,4),    # hourglass
        (238,4),    # flag
        (250,2),    # clock
        (252,2),    # bellows
    ]

    _animated_tile_cache: Dict[int, Sprite] = None

    def build_animated_tile_sprites(self) -> Dict[int, Sprite]:
        if AnimatedTileFactory._animated_tile_cache is None:
            AnimatedTileFactory._animated_tile_cache = {}
            for tile_id, num_frames in AnimatedTileFactory.animated_tiles:
                s = Sprite()
                assert 0 == len(s.frames), f"Expected to be initialised with 0 frames but have {len(s.frames)}."
                for x in range(num_frames):
                    s.frames.append(self.tileset.tiles[tile_id + x])
                assert num_frames == len(s.frames), f"Expected {num_frames} frames but built {len(s.frames)}."

                if num_frames < 3:
                    s.frame_time = 0.5
                else:
                    s.frame_time = 0.3
                AnimatedTileFactory._animated_tile_cache[tile_id] = s
                del s
        return AnimatedTileFactory._animated_tile_cache

