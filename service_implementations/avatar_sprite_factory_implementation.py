from data.global_registry import GlobalRegistry

from models.enums.transport_mode import TransportMode
from models.sprite import Sprite
from models.tile import Tile

#
# TODO: These are just regular-ass sprites.  This can be a loader.
#
class AvatarSpriteFactoryImplementation:

    # Injectable
    global_registry: GlobalRegistry
    cache = dict[tuple[TransportMode, int], Sprite]()

    # --- Factory function for the Avatar sprites ---
    def create_player(self, transport_mode: TransportMode, direction: int) -> Sprite[Tile]:
        key = transport_mode, direction
        if not key in self.cache.keys():
            func = getattr(self, f"create_player_{transport_mode.name.lower()}")
            self.cache[key] = func(direction)
        return self.cache[key]

    def _create_player_any(self, player_first_tile:int, player_frame_count:int) -> Sprite[Tile]:
        frames: list[Tile] = [self.global_registry.tiles.get(tile_id) for tile_id in range(player_first_tile, player_first_tile + player_frame_count)]
        return Sprite[Tile](frames)

    def create_player_walk(self,  _: int) -> Sprite[Tile]:
        sprite = self._create_player_any(332, 4)
        sprite.set_randomized_frame_durations()
        return sprite

    def create_player_horse(self, direction: int) -> Sprite[Tile]:
        return self._create_player_any(274 + direction, 1)

    def create_player_carpet(self, direction: int) -> Sprite[Tile]:
        return self._create_player_any(276 + direction, 1)

    def create_player_skiff(self, direction: int) -> Sprite[Tile]:
        return self._create_player_any(296 + direction, 1)

    def create_player_ship(self, direction: int) -> Sprite[Tile]:
        return self._create_player_any(292 + direction, 1)

    def create_player_sail(self, direction: int) -> Sprite[Tile]:
        return self._create_player_any(288 + direction, 1)