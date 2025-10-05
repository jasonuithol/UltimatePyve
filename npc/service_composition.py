from dark_libraries.service_provider import ServiceProvider

from .npc_registry       import NpcRegistry
from .npc_sprite_factory import NpcSpriteFactory
from .monster_spawner    import MonsterSpawner

def compose(provider: ServiceProvider):
    provider.register(NpcRegistry)    
    provider.register(NpcSpriteFactory)
    provider.register(MonsterSpawner)

    #
    # TODO: THIS IS BAD
    #
#    provider.register_mapping(NpcSpawner, MonsterSpawner)
