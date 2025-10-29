# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from service_implementations.display_service_implementation import DisplayServiceImplementation

from .console_service   import ConsoleService
from .display_service import DisplayService
from .font_mapper       import FontMapper
from .avatar_sprite_factory    import AvatarSpriteFactory
from .field_of_view_calculator import FieldOfViewCalculator
from .info_panel_data_provider import InfoPanelDataProvider
from .info_panel_service import InfoPanelService
from .lighting_service import LightingService

from .door_instance_factory    import DoorInstanceFactory

from .input_service import InputService
from .monster_service import MonsterService
from .monster_spawner     import MonsterSpawner
from .combat_map_service import CombatMapService
from .npc_service import NpcService

from .modding_service     import ModdingService

from .sfx_library_service import SfxLibraryService
from .sound_service import SoundService
from .surface_factory import SurfaceFactory
from .view_port_data_provider import ViewPortDataProvider
from .view_port_service import ViewPortService
from .world_clock import WorldClock

# Service Implementations 
from service_implementations.npc_service_implementation import NpcServiceImplementation

from .map_cache.service_composition  import compose as compose_map_cache
from .world_loot.service_composition import compose as compose_world_loot

def compose(provider: ServiceProvider):

    provider.register_mapping(NpcService, NpcServiceImplementation)
    provider.register_mapping(DisplayService, DisplayServiceImplementation)

    provider.register(SurfaceFactory)
    provider.register(AvatarSpriteFactory)
    provider.register(ConsoleService)
    provider.register(DoorInstanceFactory)
    # TODO: World Loot might be a service
    provider.register(FieldOfViewCalculator)

    provider.register(LightingService)
    provider.register(ModdingService)
    provider.register(MonsterSpawner)
    provider.register(SoundService)

    provider.register(WorldClock)
    provider.register(FontMapper)
    provider.register(CombatMapService)

    provider.register(ViewPortDataProvider)
    provider.register(ViewPortService)
    provider.register(InputService)
    provider.register(MonsterService)
    provider.register(InfoPanelService)
    provider.register(InfoPanelDataProvider)
    provider.register(SfxLibraryService)

    compose_map_cache(provider)
    compose_world_loot(provider)

