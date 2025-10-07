from enum import Enum
from models.enums.npc_ids import HumanTileId, MonsterTileId
from models.sprite import Sprite

from data.global_registry import GlobalRegistry

NUM_FRAMES = 4

class NpcSpriteBuilder:

    # Injectable
    global_registry: GlobalRegistry

    def _register_enum_sprites(self, tile_enum: type[Enum], num_frames: int):
        for enum_name, enum_value in tile_enum.__members__.items():
            tile_id = enum_value.value
            s = Sprite(
                frames      = [self.global_registry.tiles.get(i) for i in range(tile_id, tile_id + num_frames)],
                frame_time  = 0.5 if num_frames < 3 else 0.3
            )
            self.global_registry.sprites.register(tile_id, s)
            print(f"[sprites] Registered animated {tile_enum.__name__} {enum_name} with {num_frames} frames.")

    def register_npc_sprites(self):
        self._register_enum_sprites(HumanTileId, NUM_FRAMES)
        self._register_enum_sprites(MonsterTileId, NUM_FRAMES)