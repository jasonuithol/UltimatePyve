from dark_libraries.service_provider import ServiceProvider

from .map_content_registry import MapContentRegistry

def compose(provider: ServiceProvider):
    provider.register(MapContentRegistry)