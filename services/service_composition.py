# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from services.console_service   import ConsoleService
from services.display_service import DisplayService
from services.font_mapper       import FontMapper
from services.avatar_sprite_factory    import AvatarSpriteFactory
from services.field_of_view_calculator import FieldOfViewCalculator
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService
from services.lighting_service import LightingService

from services.door_instance_factory    import DoorInstanceFactory

from services.main_loop_service import MainLoopService
from services.monster_service import MonsterService
from services.monster_spawner     import MonsterSpawner
from services.combat_map_service import CombatMapService
from services.npc_service import NpcService

from services.modding_service     import ModdingService

from services.sound_service import SoundService
from services.surface_factory import SurfaceFactory
from services.world_clock import WorldClock

from .map_cache.service_composition  import compose as compose_map_cache
from .world_loot.service_composition import compose as compose_world_loot

def compose(provider: ServiceProvider):

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
    provider.register(NpcService)

    provider.register(WorldClock)
    provider.register(FontMapper)
    provider.register(CombatMapService)

    provider.register(DisplayService)
    provider.register(MainLoopService)
    provider.register(MonsterService)
    provider.register(InfoPanelService)
    provider.register(InfoPanelDataProvider)

    compose_map_cache(provider)
    compose_world_loot(provider)

