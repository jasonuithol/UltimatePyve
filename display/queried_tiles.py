from animation.sprite_registry import SpriteRegistry
from dark_libraries.custom_decorators import auto_init, immutable

from animation.sprite import Sprite
from dark_libraries.dark_math import Coord, Rect
from game.interactable.interactable_factory_registry import InteractableFactoryRegistry
from game.terrain.terrain import Terrain
from game.terrain.terrain_registry import TerrainRegistry
from maps.u5map import U5Map

from .tileset import TILE_ID_GRASS, Tile, TileRegistry

@immutable
@auto_init
class QueriedTile:
    tile: Tile
    terrain: Terrain
    sprite: Sprite | None

QueriedTileResult = dict[Coord, QueriedTile]

class QueriedTileGenerator:

    interactable_factory_registry: InteractableFactoryRegistry
    tile_registry: TileRegistry
    sprite_registry: SpriteRegistry
    terrain_registry: TerrainRegistry

    def init(self):
        self.queried_tile_grass = QueriedTile(
            tile    = self.tile_registry.tiles[TILE_ID_GRASS],
            terrain = self.terrain_registry.get_terrain(TILE_ID_GRASS),
            sprite  = None
        )

    def query_tile_grid(self, u5map: U5Map, level_ix: int, view_rect: Rect, skip_interactables: bool = False) -> QueriedTileResult:

        if not skip_interactables:
            correct_level_interactables_loaded = u5map.location_metadata.location_index == self.interactable_factory_registry.location_index and level_ix == self.interactable_factory_registry.level_index
            assert correct_level_interactables_loaded, "InteractableFactoryRegistry.load_level(u5map, level_ix) for supplied level parameters must be called first !"

        result = QueriedTileResult() 
        for world_coord in view_rect:

            # Don't try to pull a tile from outside the source map.
            # If out of bounds, use grass tile.
            if not u5map.is_in_bounds(world_coord):
                result[world_coord] = self.queried_tile_grass
                continue

            # Allow interactables to change what state an object is e.g. allow doors to open/close/unlock
            # or chests to have loot stacks on them (i.e. be open)

            # Assume there is no interactable, and pretend it's just an invisible one.
            tile_id: int = None

            if not skip_interactables:
                interactable = self.interactable_factory_registry.get_interactable(world_coord)
                if interactable:
                    # Allow get_current_tile_id to return None to signify that the container/interactable is hidden/invisible.
                    tile_id: int = interactable.get_current_tile_id()
                    '''
                    sprite = interactable.create_sprite()
                    self.draw_sprite(world_coord, sprite)
                    continue
                    '''

            if tile_id is None:
                tile_id = u5map.get_tile_id(level_ix, world_coord)

            # Don't try to render a non-existant tile id.
            assert 0 <= tile_id < len(self.tile_registry.tiles), f"tile id {tile_id!r} out of range."

            result[world_coord] = QueriedTile(
                tile = self.tile_registry.tiles[tile_id],
                terrain = self.terrain_registry.get_terrain(tile_id),
                # if the tile_id is animated, pull a frame tile from the sprite and draw that instead.
                sprite = self.sprite_registry.get_sprite(tile_id)
            )

        return result
