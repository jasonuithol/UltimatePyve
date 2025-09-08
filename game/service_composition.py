# file: game/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from game.interactable import InteractableState
from game.player_state import PlayerState
from game.terrain_factory import TerrainFactory
from game.terrain_registry import TerrainRegistry
from game.transport_mode_registry import TransportModeRegistry

def compose(provider: ServiceProvider):
    provider.register(InteractableState)
    provider.register(PlayerState)
    provider.register(TransportModeRegistry)
    provider.register(TerrainRegistry)        
    provider.register(TerrainFactory)    