# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from view.border_drawer_factory import BorderDrawerFactory
from view.info_panel import InfoPanel

from .display_config      import DisplayConfig
from .interactive_console import InteractiveConsole
from .view_port           import ViewPort
from .main_display        import MainDisplay

def compose(provider: ServiceProvider):
    provider.register(DisplayConfig)
    provider.register(ViewPort)
    provider.register(InteractiveConsole)
    provider.register(MainDisplay)
    provider.register(InfoPanel)
    provider.register(BorderDrawerFactory)
    
