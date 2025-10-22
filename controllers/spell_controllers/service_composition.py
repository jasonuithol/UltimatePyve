from dark_libraries.service_provider import ServiceProvider

from .general_spell_controller import GeneralSpellController
from .party_member_spell_controller import PartyMemberSpellController

def compose(provider: ServiceProvider):
    provider.register(GeneralSpellController)
    provider.register(PartyMemberSpellController)

