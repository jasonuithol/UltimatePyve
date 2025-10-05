from dark_libraries.service_provider import ServiceProvider

from .light_map_registry import LightMapRegistry
from .light_map_builder import LightMapBuilder
from .light_map_baker import LevelLightMapBaker
from .lighting_calculator import LightingCalculator

def compose(provider: ServiceProvider):
    provider.register(LightMapRegistry)
    provider.register(LightMapBuilder)
    provider.register(LevelLightMapBaker)
    provider.register(LightingCalculator)
    