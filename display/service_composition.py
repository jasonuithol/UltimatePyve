# file: display/service_composition.py
from dark_libraries.dark_math import Size
from dark_libraries.service_provider import ServiceProvider
from display.interactive_console import InteractiveConsole

from .display_engine import DisplayEngine
from .view_port import ViewPort
from .main_display import MainDisplay
from .u5_font import U5FontLoader

def compose(provider: ServiceProvider):
    provider.register(ViewPort)
    provider.register(MainDisplay)
    provider.register(DisplayEngine)
    provider.register(U5FontLoader)


    u5_font_loader = U5FontLoader()
    ascii_font = u5_font_loader.load("IBM.ch", Size(8,8))
    rune_font = u5_font_loader.load("RUNES.ch", Size(8,8))
    provider.register_instance(InteractiveConsole(ascii_font, rune_font))
