from dark_libraries.service_provider import ServiceProvider

from .general_spell_controller      import GeneralSpellController
from .party_member_spell_controller import PartyMemberSpellController
from .directional_spell_controller  import DirectionalSpellController
from .coordinate_spell_controller   import CoordinateSpellController

def compose(provider: ServiceProvider):
    provider.register(GeneralSpellController)
    provider.register(PartyMemberSpellController)
    provider.register(DirectionalSpellController)
    provider.register(CoordinateSpellController)

