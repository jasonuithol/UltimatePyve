# file: display/service_composition.py
from animation.animated_tile_factory import AnimatedTileFactory
from dark_libraries.service_provider import ServiceProvider
from display.display_engine import DisplayEngine
from display.view_port import ViewPort
from display.main_display import MainDisplay

def compose(provider: ServiceProvider):
    provider.register(ViewPort)
    provider.register(MainDisplay)
    provider.register(AnimatedTileFactory)
    provider.register(DisplayEngine)
