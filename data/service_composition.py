# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from data.global_registry import GlobalRegistry
from data.global_registry_loader import GlobalRegistryLoader

from .loaders.service_composition import compose as compose_loaders

def compose(provider: ServiceProvider):
    
    provider.register(GlobalRegistry)
    provider.register(GlobalRegistryLoader)

    compose_loaders(provider)
