from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from data.loaders.entry_trigger_loader import EntryTriggerLoader
from data.loaders.tileset_loader       import TileLoader
from data.loaders.terrain_loader       import TerrainLoader
from data.loaders.transport_mode_loader import TransportModeLoader
from data.loaders.u5_map_loader         import U5MapLoader
from data.loaders.animated_tile_loader import AnimatedTileLoader
from data.loaders.door_type_loader     import DoorTypeLoader
from data.loaders.flame_sprite_loader  import FlameSpriteLoader

from data.loaders.consumable_item_type_loader import ConsumableItemTypeLoader
from data.loaders.equipable_item_type_loader  import EquipableItemTypeLoader

from data.registries.registry_base import Registry
from services.light_map_level_baker import LightMapLevelBaker
from data.loaders.light_map_builder     import LightMapBuilder
from data.loaders.npc_sprite_builder    import NpcSpriteBuilder

# TODO: Fix
from data.loaders.u5_font_loader import U5FontLoader
from data.loaders.u5_glyph_loader import U5GlyphLoader

from services.modding_service import ModdingService

class GlobalRegistryLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    tile_loader:                 TileLoader
    terrain_loader:              TerrainLoader
    u5map_loader:                U5MapLoader
    entry_trigger_loader:        EntryTriggerLoader

    animated_tile_loader:        AnimatedTileLoader
    flame_sprite_loader:         FlameSpriteLoader

    door_type_loader:            DoorTypeLoader

    equipable_item_type_loader:  EquipableItemTypeLoader
    consumable_item_type_loader: ConsumableItemTypeLoader

    u5_font_loader:              U5FontLoader
    u5_glyph_loader:             U5GlyphLoader
    light_map_builder:           LightMapBuilder
    light_map_level_baker:       LightMapLevelBaker
#    saved_game_loader: SavedGameLoader
    npc_sprite_builder:          NpcSpriteBuilder
    transport_mode_loader:       TransportModeLoader

    modding: ModdingService

    def _post_load_check(self) -> bool:
        all_registries_loaded = True
        for name, registry in self.global_registry.__dict__.items():
            if isinstance(registry, Registry):
                if len(registry) == 0:
                    self.log(f"ERROR: {name} registry is empty.")
                    all_registries_loaded = False
        return all_registries_loaded

    def load(self):

        # Map
        self.tile_loader.load_tiles()
        self.terrain_loader.register_terrains()
        self.u5map_loader.register_maps()
        self.entry_trigger_loader.load()

        self.animated_tile_loader.register_sprites()
        self.flame_sprite_loader.register_sprites()

        # font
        self.u5_font_loader.register_fonts()
        self.u5_glyph_loader.register_glyphs()

        # NOTE: this will include chests, orientable furniture, maybe movable furniture ?
        #       one day maybe even the avatar's transports could be these ?
        self.door_type_loader.load()

        self.equipable_item_type_loader.build()
        self.consumable_item_type_loader.register_item_types()

        # display
        self.light_map_builder.build_light_maps()

        # npc
        self.npc_sprite_builder.register_npc_sprites()
        self.transport_mode_loader.load()

        #
        # TODO: LOAD REGISTRY SPECIFIC MODS AFTER EACH OG REGISTRY IS LOADED.
        #
#        self.modding.load_mods()

        if self._post_load_check():
            self.log("All registries loaded.")
        else:
            self.log("WARNING: Some registries did not load.")


        
                

