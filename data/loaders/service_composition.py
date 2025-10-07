from dark_libraries.service_provider import ServiceProvider

from data.loaders.animated_tile_loader        import AnimatedTileLoader
from data.loaders.consumable_item_type_loader import ConsumableItemTypeLoader
from data.loaders.door_type_loader            import DoorTypeLoader
from data.loaders.entry_trigger_loader        import EntryTriggerLoader

from data.loaders.equipable_item_type_loader  import EquipableItemTypeLoader
from data.loaders.flame_sprite_loader         import FlameSpriteLoader
from data.loaders.light_map_builder           import LightMapBuilder
from services.light_map_level_baker       import LightMapLevelBaker

from data.loaders.npc_sprite_builder        import NpcSpriteBuilder
from data.loaders.overworld                 import load_britannia
from data.loaders.terrain_loader            import TerrainLoader

from data.loaders.tileset_loader        import TileLoader
from data.loaders.transport_mode_loader import TransportModeLoader
from data.loaders.u5_font_loader        import U5FontLoader
from data.loaders.u5_glyph_loader       import U5GlyphLoader

from data.loaders.location_metadata_builder import LocationMetadataBuilder
from data.loaders.u5_map_loader     import U5MapLoader
from data.loaders.underworld        import load_underworld


def compose(provider: ServiceProvider):

    provider.register(AnimatedTileLoader)
    provider.register(ConsumableItemTypeLoader)
    provider.register(DoorTypeLoader)
    provider.register(EntryTriggerLoader)

    provider.register(EquipableItemTypeLoader)
    provider.register(FlameSpriteLoader)
    provider.register(LightMapLevelBaker)
    provider.register(LightMapBuilder)

    provider.register(NpcSpriteBuilder)
    provider.register_instance(load_britannia())
    provider.register(TerrainLoader)

    provider.register(TileLoader)
    provider.register(TransportModeLoader)
    provider.register(U5FontLoader)
    provider.register(U5GlyphLoader)

    provider.register(LocationMetadataBuilder)
    provider.register(U5MapLoader)
    provider.register_instance(load_underworld())
