from .sprite import Sprite
from loaders import TileSet


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