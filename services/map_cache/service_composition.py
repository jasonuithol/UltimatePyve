# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from services.map_cache.map_cache_service import MapCacheService

def compose(provider: ServiceProvider):
    provider.register(MapCacheService)
