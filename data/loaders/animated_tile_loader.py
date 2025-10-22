from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.sprite import Sprite
from models.tile import Tile

class AnimatedTileLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

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
            s = Sprite[Tile](
                [self.global_registry.tiles.get(i) for i in range(tile_id, tile_id + num_frames)],
                0.5 if num_frames < 3 else 0.3
            )
            self.global_registry.sprites.register(tile_id, s)
            self.log(f"DEBUG: Registered animated terrain for base tile_id={tile_id} with {num_frames} frames.")
        self.log(f"Registered {len(self.animated_tiles)} animated terrain sprites.")