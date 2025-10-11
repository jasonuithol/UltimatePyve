from dark_libraries.dark_math      import Coord
from data.registries.registry_base import Registry

from models.combat_map import CombatMap, DungeonRoom
from models.door_type import DoorType
from models.npc_metadata import NpcMetadata
from models.u5_font    import U5Font
from models.tile       import Tile
from models.sprite     import Sprite
from models.terrain    import Terrain

from models.u5_map     import U5Map
from models.item_type  import ItemType
from models.world_item import WorldItem

from models.light_map       import LightMap
from models.u5_glyph        import U5Glyph
from models.global_location import GlobalLocation
from models.interactable    import Interactable

class GlobalRegistry:

    def _after_inject(self):
        
        # map oriented features.
        self.tiles    = Registry[int, Tile]()     # tile_id
        self.maps     = Registry[int, U5Map]()    # location_index
        self.sprites  = Registry[int, Sprite]()   # tile_id
        self.terrains = Registry[int, Terrain]()  # tile_id

        self.entry_triggers = Registry[GlobalLocation, GlobalLocation]()

        # This is over-engineering, but I was getting circular imports and so this happened.
        self.door_types     = Registry[int,            DoorType]()

        self.interactables  = Registry[Coord,          Interactable](can_be_empty=True)

        # item oriented features.
        self.item_types = Registry[int, ItemType]() # item_id (NOT InventoryOffset ?!?!?!)
        self.world_loot = Registry[GlobalLocation, WorldItem]()

        # player oriented features.
        self.transport_modes = Registry[int, str]() # transport_mode_index

        # display oriented features.
        self.fonts                  = Registry[str,             U5Font]()     # font_name
        self.font_glyphs            = Registry[tuple[str, int], U5Glyph]()    # (font_name, glyph_code)
        self.unbaked_light_maps     = Registry[int,             LightMap]()   # radius
        self.baked_light_level_maps = Registry[tuple[int,int],  dict[Coord, LightMap]]()   # location, level -> coord, lightmap

        # soundtracks.
        self.location_soundtracks  = Registry[int, str](can_be_empty=True) # location_index
        self.transport_soundtracks = Registry[int, str](can_be_empty=True) # transport_mode_index

        self.combat_maps   = Registry[int, CombatMap]()
        self.dungeon_rooms = Registry[int, DungeonRoom]()
        self.npc_metadata  = Registry[int, NpcMetadata]()
