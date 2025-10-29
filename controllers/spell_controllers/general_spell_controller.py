from datetime import timedelta

from dark_libraries.logging import LoggerMixin

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.spell_type import SpellType

from services.world_clock import WorldClock

class GeneralSpellController(LoggerMixin):

    party_agent: PartyAgent
    world_clock: WorldClock

    def cast(self, spell_caster: PartyMemberAgent, spell_type: SpellType) -> bool:

        # LEVEL ONE
        if spell_type.spell_key == "il":
            self.party_agent.set_light(radius = 3, expiry = self.world_clock.get_natural_time() + timedelta(hours = 4))

        # LEVEL TWO


        else:
            assert False, f"Unknown spell_key={spell_type.spell_key} for {__class__.__name__}"