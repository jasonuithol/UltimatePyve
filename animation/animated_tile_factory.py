from typing import Dict
from animation.sprite import Sprite
from animation.sprite_registry import SpriteRegistry
from loaders.tileset import TileSet

class AnimatedTileFactory:

    # Injectable
    tileset: TileSet
    sprite_registry: SpriteRegistry

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

    def register_sprites(self):
        for tile_id, num_frames in self.animated_tiles:
            s = Sprite()
            assert 0 == len(s.frames), f"Expected to be initialised with 0 frames but have {len(s.frames)}."
            for x in range(num_frames):
                s.frames.append(self.tileset.tiles[tile_id + x])
            assert num_frames == len(s.frames), f"Expected {num_frames} frames but built {len(s.frames)}."

            if num_frames < 3:
                s.frame_time = 0.5
            else:
                s.frame_time = 0.3
            self.sprite_registry.register_animated_tile(tile_id, s)
        
