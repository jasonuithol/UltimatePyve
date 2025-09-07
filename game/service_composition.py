# file: game/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from game.interactable import InteractableState
from game.player_state import PlayerState


def compose(provider: ServiceProvider):
    provider.register(InteractableState)
    provider.register(PlayerState)
    