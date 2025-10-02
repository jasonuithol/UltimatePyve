from .sprite import Sprite
from .sprite_registry import SpriteRegistry
from display.tileset import TileRegistry

class AnimatedTileFactory:

    # Injectable
    tileset: TileRegistry
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
            s = Sprite(
                frames      = [self.tileset.tiles[i] for i in range(tile_id, tile_id + num_frames)],
                frame_time  = 0.5 if num_frames < 3 else 0.3
            )
            self.sprite_registry.register_animated_tile(tile_id, s)
            print(f"[sprites] Registered animated terrain for base tile_id={tile_id} with {num_frames} frames.")