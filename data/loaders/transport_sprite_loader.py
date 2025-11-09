from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.enums.transport_mode import PlayerTransportTileId
from models.sprite import Sprite

class TransportSpriteLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def load(self):
        before = len(self.global_registry.sprites)
        for tile_id_enum in PlayerTransportTileId:
            frame = self.global_registry.tiles.get(tile_id_enum.value)
            assert frame, f"Could not find tile for {tile_id_enum}"
            sprite = Sprite(frames = [frame])
            sprite.set_uniform_frame_duration(1.0)
            self.global_registry.sprites.register(tile_id_enum.value, sprite)
        after = len(self.global_registry.sprites)
        self.log(f"Loaded {after - before} transport sprites")