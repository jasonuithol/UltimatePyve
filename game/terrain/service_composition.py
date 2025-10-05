from dark_libraries.service_provider import ServiceProvider

from .terrain_factory  import TerrainFactory
from .terrain_registry import TerrainRegistry

def compose(provider: ServiceProvider):
    provider.register(TerrainRegistry)
    provider.register(TerrainFactory)