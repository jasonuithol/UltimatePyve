# file: animation/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .display_controller        import DisplayController
from .initialisation_controller import InitialisationController
from .main_loop_controller      import MainLoopController
from .party_controller          import PartyController
from .combat_controller         import CombatController
from .monster_controller        import MonsterController

def compose(provider: ServiceProvider):
    provider.register(DisplayController)
    provider.register(InitialisationController)
    provider.register(MainLoopController)
    provider.register(PartyController)
    provider.register(CombatController)
    provider.register(MonsterController)

