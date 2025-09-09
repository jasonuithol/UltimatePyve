# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .display_engine import DisplayEngine
from .view_port import ViewPort
from .main_display import MainDisplay

def compose(provider: ServiceProvider):
    provider.register(ViewPort)
    provider.register(MainDisplay)
    provider.register(DisplayEngine)
