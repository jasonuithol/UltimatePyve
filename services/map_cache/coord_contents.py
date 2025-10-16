from dark_libraries.service_provider import ServiceProvider
from data.global_registry            import GlobalRegistry

from models.tile         import Tile
from models.sprite       import Sprite
from models.terrain      import Terrain
from models.interactable import Interactable

class CoordContents:

    def __init__(self, tile: Tile, terrain: Terrain, sprite: Sprite):

        self.tile = tile
        self.terrain = terrain
        self.terrain_sprite = sprite
        if not sprite is None:
            self.terrain_sprite_time_offset = sprite.create_random_time_offset()
        self.terrain_interactable: Interactable = None

        self.global_registry: GlobalRegistry = ServiceProvider.get_provider().resolve(GlobalRegistry)

    def set_terrain_interactable(self, terrain_interactable: Interactable):
        self.terrain_interactable = terrain_interactable

    def get_terrain(self) -> Terrain:

        # We don't care about terrain_sprite.

        if not self.terrain_interactable is None:
            # a door, or pile of loot is here.
            tile_id = self.terrain_interactable.get_current_tile_id()
            return self.global_registry.terrains.get(tile_id)

        # just dirt, rocks, wall, water, some other geographic or architectural thing.
        return self.terrain

    def get_renderable_frame(self) -> Tile:

        if not self.terrain_interactable is None:
            return self.terrain_interactable.get_current_tile_id()

        if not self.terrain_sprite is None:
            return self.terrain_sprite.get_current_frame_tile(self.terrain_sprite_time_offset)

        return self.tile