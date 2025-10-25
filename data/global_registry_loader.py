from pathlib import Path
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from data.loaders.blue_border_glyph_factory import BlueBorderGlyphFactory
from data.loaders.combat_map_loader     import CombatMapLoader
from data.loaders.cursor_loader import CursorLoader
from data.loaders.data_ovl_loader import DataOVLLoader
from data.loaders.entry_trigger_loader  import EntryTriggerLoader
from data.loaders.npc_metadata_loader   import NpcMetadataLoader
from data.loaders.projectile_loader import ProjectileLoader
from data.loaders.save_game_loader      import SavedGameLoader

from data.loaders.scroll_border_glyph_factory import ScrollBorderGlyphFactory
from data.loaders.spell_rune_loader import SpellRuneLoader
from data.loaders.spell_type_loader import SpellTypeLoader
from data.loaders.tileset_loader        import TileLoader
from data.loaders.terrain_loader        import TerrainLoader
from data.loaders.transport_mode_loader import TransportModeLoader
from data.loaders.u5_map_loader         import U5MapLoader

from data.loaders.animated_tile_loader  import AnimatedTileLoader
from data.loaders.door_type_loader      import DoorTypeLoader
from data.loaders.flame_sprite_loader   import FlameSpriteLoader

from data.loaders.consumable_item_type_loader import ConsumableItemTypeLoader
from data.loaders.equipable_item_type_loader  import EquipableItemTypeLoader

from dark_libraries.registry   import Registry
from data.loaders.light_map_builder  import LightMapBuilder
from data.loaders.npc_sprite_builder import NpcSpriteBuilder

# TODO: Fix
from data.loaders.u5_font_loader  import U5FontLoader
from data.loaders.u5_glyph_loader import U5GlyphLoader

from services.modding_service import ModdingService
from services.light_map_level_baker  import LightMapLevelBaker

class GlobalRegistryLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    data_ovl_loader: DataOVLLoader

    tile_loader:                 TileLoader
    terrain_loader:              TerrainLoader
    u5map_loader:                U5MapLoader
    entry_trigger_loader:        EntryTriggerLoader

    animated_tile_loader:        AnimatedTileLoader
    flame_sprite_loader:         FlameSpriteLoader
    cursor_loader:               CursorLoader

    door_type_loader:            DoorTypeLoader

    equipable_item_type_loader:  EquipableItemTypeLoader
    consumable_item_type_loader: ConsumableItemTypeLoader

    u5_font_loader:              U5FontLoader
    u5_glyph_loader:             U5GlyphLoader
    light_map_builder:           LightMapBuilder
    light_map_level_baker:       LightMapLevelBaker
    npc_sprite_builder:          NpcSpriteBuilder
    transport_mode_loader:       TransportModeLoader

    combat_map_loader:           CombatMapLoader
    npc_metadata_loader:         NpcMetadataLoader
    saved_game_loader:           SavedGameLoader

    blue_border_glyph_factory:   BlueBorderGlyphFactory
    scroll_border_glyph_factory: ScrollBorderGlyphFactory

    spell_rune_loader: SpellRuneLoader
    spell_type_loader: SpellTypeLoader

    projectile_loader: ProjectileLoader

    modding: ModdingService

    def _post_load_check(self) -> bool:
        all_registries_loaded = True
        for name, registry in self.global_registry.__dict__.items():
            if isinstance(registry, Registry):
                if len(registry) == 0:
                    if registry._can_be_empty == False:
                        self.log(f"ERROR: {name} registry is empty (len == 0).")
                        all_registries_loaded = False
                    continue
            else:
                if registry is None:
                        self.log(f"ERROR: {name} property is unassigned (None).")

        return all_registries_loaded

    def load(self, u5_path: Path):

        self.data_ovl_loader.load(u5_path)

        # Map
        self.tile_loader.load_tiles(u5_path)
        self.terrain_loader.register_terrains()
        self.u5map_loader.register_maps(u5_path)
        self.entry_trigger_loader.load()

        self.animated_tile_loader.register_sprites()
        self.flame_sprite_loader.register_sprites()

        self.combat_map_loader.load(u5_path)

        # font
        self.u5_font_loader.register_fonts(u5_path)
        self.u5_glyph_loader.register_glyphs()
        self.blue_border_glyph_factory.load()
        self.scroll_border_glyph_factory.load()

        # NOTE: this will include chests, orientable furniture, maybe movable furniture ?
        #       one day maybe even the avatar's transports could be these ?
        self.door_type_loader.load()

        self.equipable_item_type_loader.build()
        self.consumable_item_type_loader.register_item_types()

        # display
        self.light_map_builder.build_light_maps()
        self.cursor_loader.load()

        # npc
        self.npc_sprite_builder.register_npc_sprites()
        self.transport_mode_loader.load()
        self.npc_metadata_loader.load()

        # magic
        self.spell_rune_loader.load()
        self.spell_type_loader.load()

        self.projectile_loader.load()

        self.saved_game_loader.load_existing(u5_path)

        #
        # TODO: LOAD REGISTRY SPECIFIC MODS AFTER EACH OG REGISTRY IS LOADED.
        #
#        self.modding.load_mods()

        if self._post_load_check():
            self.log("All registries loaded.")
        else:
            self.log("WARNING: Some registries did not load.")


        
                

