from dark_libraries.service_provider import ServiceProvider

from animation.sprite_registry   import SpriteRegistry
from animation.sprite            import Sprite
from npc.npc_interactable        import NpcInteractable
from display.tileset             import Tile, TileRegistry

from ..interactable.interactable import Interactable
from ..terrain.terrain           import Terrain
from ..terrain.terrain_registry  import TerrainRegistry

class Registries:
    def __init__(self):
        self.terrain_registry: TerrainRegistry = ServiceProvider.get_provider().resolve(TerrainRegistry)
        self.sprite_registry: SpriteRegistry   = ServiceProvider.get_provider().resolve(SpriteRegistry)
        self.tile_registry: TileRegistry       = ServiceProvider.get_provider().resolve(TileRegistry)

_registries: Registries = None

class CoordContents:

    def __init__(self, tile_id: int):

        #
        # TODO: A horrible hack I'm sure I'll pay for later.
        #
        global _registries
        if _registries is None:
            _registries = Registries()

        self.tile: Tile = _registries.tile_registry.get_tile(tile_id)
        self.terrain_sprite: Sprite | None = _registries.sprite_registry.get_sprite(tile_id)
#        self.terrain_sprite: Sprite | None = _registries.terrain_registry.get_terrain(tile_id)

        # TODO: Do we front-load this ?
        self.terrain_interactable: Interactable | None = None

        #
        # TODO: In an alternate universe, NPCs have nothing to do with map content.
        #
        self.npc: NpcInteractable | None = None

    def set_terrain_interactable(self, terrain_interactable: Interactable):
        self.terrain_interactable = terrain_interactable

    def set_npc(self, npc: NpcInteractable):
        self.npc = npc

    def get_terrain(self) -> Terrain:

        '''
        if not self.npc is None:
            # an NPC or something is there, no terrain activity allowed.
            return Terrain()
        '''

        # We don't care about terrain_sprite.

        if not self.terrain_interactable is None:
            # a door, or pile of loot is here.
            return _registries.terrain_registry.get_terrain(self.terrain_interactable.get_current_tile_id())

        # just dirt, rocks, wall, water, some other geographic or architectural thing.
        return _registries.terrain_registry.get_terrain(self.tile.tile_id)

    def is_occupied(self) -> bool:
        return not self.npc is None

    def get_renderable_frame(self) -> Tile:

        if not self.npc is None:
            return self.npc.sprite.get_current_frame_tile()

        if not self.terrain_interactable is None:
            return self.terrain_interactable.get_current_tile_id()

        if not self.terrain_sprite is None:
            return self.terrain_sprite.get_current_frame_tile()

        return self.tile