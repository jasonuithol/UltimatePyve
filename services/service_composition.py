# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from services.avatar_sprite_factory    import AvatarSpriteFactory
from services.console_service          import ConsoleService
from services.door_instance_factory    import DoorInstanceFactory
from services.field_of_view_calculator import FieldOfViewCalculator

from services.font_mapper import FontMapper
from services.lighting_service import LightingService
from services.modding_service     import ModdingService
from services.monster_spawner     import MonsterSpawner
from services.sound_track_player  import SoundTrackPlayer

from services.world_clock import WorldClock

from .map_cache.service_composition import compose as compose_map_cache
from .world_loot.service_composition import compose as compose_world_loot

def compose(provider: ServiceProvider):

    provider.register(AvatarSpriteFactory)
    provider.register(ConsoleService)
    provider.register(DoorInstanceFactory)
    # TODO: World Loot might be a service
    provider.register(FieldOfViewCalculator)

    provider.register(LightingService)
    provider.register(ModdingService)
    provider.register(MonsterSpawner)
    provider.register(SoundTrackPlayer)

    provider.register(WorldClock)
    provider.register(FontMapper)

    compose_map_cache(provider)
    compose_world_loot(provider)

