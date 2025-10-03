from dark_libraries.service_provider import ServiceProvider

from .npcs import NpcRegistry, NpcSpawner, NpcSpriteFactory
from .monsters import MonsterSpawner


def compose(provider: ServiceProvider):
    provider.register(NpcRegistry)    
    provider.register(NpcSpriteFactory)
#    provider.register(MonsterSpawner)
    provider.register_mapping(NpcSpawner, MonsterSpawner)
