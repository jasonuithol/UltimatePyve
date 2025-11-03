import random

from dark_libraries.logging import LoggerMixin

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.spell_type import SpellType

from services.console_service import ConsoleService
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService

from services.input_service import InputService
from services.npc_service import NpcService
from services.sfx_library_service import SfxLibraryService

class PartyMemberSpellController(LoggerMixin):

    party_agent: PartyAgent
    input_service: InputService
    npc_service: NpcService
    sfx_library_service: SfxLibraryService
    console_service: ConsoleService
    info_panel_data_provider: InfoPanelDataProvider
    info_panel_service: InfoPanelService
    
    def cast(self, spell_caster: PartyMemberAgent, spell_type: SpellType) -> bool:

        self.console_service.print_ascii("On who: ", include_carriage_return = False)
        party_data = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_data, select_mode = True)

        target_party_member_index = self.info_panel_service.choose_item(party_data.party_data_set, 0)
        if target_party_member_index is None:
            return False
        
        target_member = self.party_agent.get_party_member(target_party_member_index)
        self.console_service.print_ascii(target_member.name, no_prompt = True)

        self.sfx_library_service.cast_spell_normal()
        self._apply_spell_effects(spell_caster, spell_type, target_member)

        return True

    def _apply_spell_effects(self, spell_caster: PartyMemberAgent, spell_type: SpellType, target_member: PartyMemberAgent):

        # LEVEL ONE

        if spell_type.spell_key == "m":
            amount_healed = random.randrange(1, spell_caster.intelligence)
            target_member.hitpoints = min(target_member.hitpoints + amount_healed, target_member.maximum_hitpoints)

        elif spell_type.spell_key == "an":
            target_member.cure()

        elif spell_type.spell_key == "az":
            target_member.awake()

        # LEVEL TWO

        else:
            assert False, f"Unknown spell_key={spell_type.spell_key} for {__class__.__name__}"