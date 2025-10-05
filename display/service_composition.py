# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .tileset import TileLoader, TileRegistry
from .display_config import DisplayConfig
from .interactive_console import InteractiveConsole
from .display_engine import DisplayEngine
from .view_port import ViewPort
from .main_display import MainDisplay
from .u5_font import U5FontLoader, U5FontRegistry, U5GlyphLoader, U5GlyphRegistry
from .field_of_view_calculator import FieldOfViewCalculator

from .lighting.service_composition import compose as compose_lighting

def compose(provider: ServiceProvider):
    provider.register(DisplayConfig)

    provider.register(U5FontLoader)
    provider.register(U5FontRegistry)
    provider.register(U5GlyphLoader)
    provider.register(U5GlyphRegistry)

    provider.register(TileRegistry)
    provider.register(TileLoader)

    provider.register(ViewPort)
    provider.register(InteractiveConsole)
    provider.register(MainDisplay)
    provider.register(DisplayEngine)

    provider.register(FieldOfViewCalculator)

    compose_lighting(provider)
