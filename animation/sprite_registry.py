from typing import Optional
from .sprite import Sprite

class SpriteRegistry:

    def _after_inject(self):
        self._animated_tiles: dict[int, Sprite] = dict()

    def register_animated_tile(self, tile_id: int, sprite: Sprite) -> None:
        self._animated_tiles[tile_id] = sprite

    def get_sprite(self, tile_id: int) -> Optional[Sprite]:
        return self._animated_tiles.get(tile_id, None)
