from dark_libraries.service_provider import ServiceProvider

from data.loaders.animated_tile_loader        import AnimatedTileLoader
from data.loaders.blue_border_glyph_factory import BlueBorderGlyphFactory
from data.loaders.color_loader import ColorLoader
from data.loaders.combat_map_loader import CombatMapLoader
from data.loaders.consumable_item_type_loader import ConsumableItemTypeLoader
from data.loaders.cursor_loader import CursorLoader
from data.loaders.data_ovl_loader import DataOVLLoader
from data.loaders.door_type_loader            import DoorTypeLoader
from data.loaders.entry_trigger_loader        import EntryTriggerLoader

from data.loaders.equipable_item_type_loader  import EquipableItemTypeLoader
from data.loaders.flame_sprite_loader         import FlameSpriteLoader
from data.loaders.light_map_builder           import LightMapBuilder
from data.loaders.npc_metadata_loader import NpcMetadataLoader
from data.loaders.projectile_sprite_loader import ProjectileSpriteLoader
from data.loaders.save_game_loader import SavedGameLoader
from data.loaders.scroll_border_glyph_factory import ScrollBorderGlyphFactory
from data.loaders.spell_rune_loader import SpellRuneLoader
from data.loaders.spell_type_loader import SpellTypeLoader
from data.loaders.transport_sprite_loader import TransportSpriteLoader
from services.light_map_level_baker       import LightMapLevelBaker

from data.loaders.npc_sprite_builder        import NpcSpriteBuilder
from data.loaders.terrain_loader            import TerrainLoader

from data.loaders.tileset_loader        import TileLoader
from data.loaders.u5_font_loader        import U5FontLoader
from data.loaders.u5_glyph_loader       import U5GlyphLoader

from data.loaders.location_metadata_builder import LocationMetadataBuilder
from data.loaders.u5_map_loader     import U5MapLoader

def compose(provider: ServiceProvider):

    provider.register(DataOVLLoader)

    provider.register(AnimatedTileLoader)
    provider.register(ConsumableItemTypeLoader)
    provider.register(DoorTypeLoader)
    provider.register(EntryTriggerLoader)

    provider.register(CombatMapLoader)

    provider.register(EquipableItemTypeLoader)
    provider.register(FlameSpriteLoader)
    provider.register(LightMapLevelBaker)
    provider.register(LightMapBuilder)
    provider.register(CursorLoader)

    provider.register(NpcSpriteBuilder)
    provider.register(TerrainLoader)

    provider.register(ColorLoader)
    provider.register(TileLoader)
    provider.register(TransportSpriteLoader)
    provider.register(U5FontLoader)
    provider.register(U5GlyphLoader)
    provider.register(BlueBorderGlyphFactory)
    provider.register(ScrollBorderGlyphFactory)

    provider.register(LocationMetadataBuilder)
    provider.register(U5MapLoader)
    provider.register(NpcMetadataLoader)
    provider.register(SavedGameLoader)
    provider.register(SpellRuneLoader)
    provider.register(SpellTypeLoader)

    provider.register(ProjectileSpriteLoader)