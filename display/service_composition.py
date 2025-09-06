# file: display/service_composition.py
from animation.sprite import AnimatedTileFactory
from dark_libraries.service_provider import ServiceProvider
from display.display_engine import DisplayEngine
from display.engine_protocol import EngineProtocol
from display.view_port import ViewPort
from display.main_display import MainDisplay

def compose(provider: ServiceProvider):
    provider.register(ViewPort)
    provider.register(MainDisplay)
    provider.register(AnimatedTileFactory)
    provider.register_mapping(EngineProtocol, DisplayEngine)