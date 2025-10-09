from dark_libraries.logging import LoggerMixin
from models.enums.npc_ids import NpcTileId
from models.sprite import Sprite

from data.global_registry import GlobalRegistry

NUM_FRAMES = 4

class NpcSpriteBuilder(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def register_npc_sprites(self):
        before = len(self.global_registry.sprites)
        for enum_member in NpcTileId:
            tile_id = enum_member.value
            s = Sprite(
                frames      = [self.global_registry.tiles.get(i) for i in range(tile_id, tile_id + NUM_FRAMES)],
                frame_time  = 0.5 if NUM_FRAMES < 3 else 0.3
            )
            self.global_registry.sprites.register(tile_id, s)
            self.log(f"DEBUG: Registered animated NPC {enum_member.name} with {NUM_FRAMES} frames.")
        after = len(self.global_registry.sprites)
        self.log(f"Registered {after - before} NPC sprites.")

