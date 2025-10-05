
from enum import Enum

from animation.sprite import Sprite
from animation.sprite_registry import SpriteRegistry
from display.tileset import TileRegistry

from .npc_ids import HumanTileId, MonsterTileId

NUM_FRAMES = 4

class NpcSpriteFactory:

    # Injectable
    tile_registry: TileRegistry
    sprite_registry: SpriteRegistry

    def _register_enum_sprites(self, tile_enum: type[Enum], num_frames: int):
        for enum_name, enum_value in tile_enum.__members__.items():
            tile_id = enum_value.value
            s = Sprite(
                frames      = [self.tile_registry.tiles[i] for i in range(tile_id, tile_id + num_frames)],
                frame_time  = 0.5 if num_frames < 3 else 0.3
            )
            self.sprite_registry.register_animated_tile(tile_id, s)
            print(f"[sprites] Registered animated {tile_enum.__name__} {enum_name} with {num_frames} frames.")

    def register_npc_sprites(self):
        self._register_enum_sprites(HumanTileId, NUM_FRAMES)
        self._register_enum_sprites(MonsterTileId, NUM_FRAMES)