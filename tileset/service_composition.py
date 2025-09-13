from dark_libraries.service_provider import ServiceProvider
from .tileset import load_tileset

def compose(provider: ServiceProvider):
    provider.register_instance(load_tileset())
