# file: animation/service_composition.py
from controllers.active_member_controller import ActiveMemberController
from controllers.cast_controller import CastController
from controllers.move_controller import MoveController
from controllers.ready_controller import ReadyController
from dark_libraries.service_provider import ServiceProvider

from .initialisation_controller import InitialisationController
from .party_controller          import PartyController
from .combat_controller         import CombatController

def compose(provider: ServiceProvider):
    provider.register(InitialisationController)
    provider.register(PartyController)
    provider.register(CombatController)
    provider.register(MoveController)
    provider.register(ActiveMemberController)
    provider.register(ReadyController)
    provider.register(CastController)

