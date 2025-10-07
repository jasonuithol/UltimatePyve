# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from services.world_loot.world_loot_service import WorldLootService

def compose(provider: ServiceProvider):
    provider.register(WorldLootService)
