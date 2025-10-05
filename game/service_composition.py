# file: game/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .player_state            import PlayerState
from .saved_game              import SavedGame, SavedGameLoader
from .soundtracks             import SoundTrackPlayer
from .transport_mode_registry import TransportModeRegistry
from .modding                 import Modding
from .world_clock             import WorldClock
from .interactable            import DoorTypeFactory, InteractableFactoryRegistry

from .terrain.service_composition         import compose as compose_terrain
from game.map_content.service_composition import compose as compose_map_content

def compose(provider: ServiceProvider):
    provider.register(DoorTypeFactory)
    provider.register(InteractableFactoryRegistry)
    provider.register(PlayerState)
    provider.register(TransportModeRegistry)
    provider.register(SavedGame)
    provider.register(SavedGameLoader)
    provider.register(Modding)
    provider.register(WorldClock)
    provider.register(SoundTrackPlayer)

    compose_terrain(provider)
    compose_map_content(provider)
    

    