# file: game/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from game import *
from game.modding import Modding
from .interactable import *
from .terrain import *

def compose(provider: ServiceProvider):
    provider.register(DoorTypeFactory)
    provider.register(InteractableFactoryRegistry)
    provider.register(PlayerState)
    provider.register(TransportModeRegistry)
    provider.register(TerrainRegistry)        
    provider.register(TerrainFactory)
    provider.register(SavedGame)
    provider.register(SavedGameLoader)
    provider.register(Modding)

    