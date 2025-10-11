from .service_provider import ServiceProvider
from .dark_events import DarkEventService

def compose(provider: ServiceProvider):
    provider.register(DarkEventService)

