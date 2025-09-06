# file: game/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from game.player_state import PlayerState
from game.world_state import WorldState


def compose(provider: ServiceProvider):
    provider.register(WorldState)
    provider.register(PlayerState)
    