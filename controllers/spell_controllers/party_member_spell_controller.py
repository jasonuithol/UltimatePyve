import random

from dark_libraries.logging import LoggerMixin

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.spell_type import SpellType

class PartyMemberSpellController(LoggerMixin):

    party_agent: PartyAgent

    def cast(self, spell_caster: PartyMemberAgent, spell_type: SpellType, target_member: PartyMemberAgent) -> bool:

        # LEVEL ONE

        if spell_type.spell_key == "m":
            amount_healed = random.randrange(1, spell_caster.intelligence)
            target_member.hitpoints = min(target_member.hitpoints + amount_healed, target_member.maximum_hitpoints)
        else:
            assert False, f"Unknown spell_key={spell_type.spell_key} for {__class__.__name__}"