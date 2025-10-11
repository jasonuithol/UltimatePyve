# file: animation/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .initialisation_controller import InitialisationController
from .party_controller          import PartyController
from .combat_controller         import CombatController

def compose(provider: ServiceProvider):
    provider.register(InitialisationController)
    provider.register(PartyController)
    provider.register(CombatController)

