from models.tile    import Tile
from models.sprite  import Sprite
from models.terrain import Terrain

class CoordContents:

    def __init__(self, tile: Tile, terrain: Terrain, sprite: Sprite[Tile]):

        self.tile = tile
        self.terrain = terrain
        self.terrain_sprite = sprite
        if not sprite is None:
            self.terrain_sprite_time_offset = sprite.create_random_time_offset()

    def get_terrain(self) -> Terrain:
        return self.terrain

    def get_renderable_frame(self) -> Tile:
        if not self.terrain_sprite is None:
            return self.terrain_sprite.get_current_frame(self.terrain_sprite_time_offset)
        return self.tile
