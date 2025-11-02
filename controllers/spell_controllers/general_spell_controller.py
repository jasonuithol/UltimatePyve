from datetime import timedelta
import random

from dark_libraries.logging import LoggerMixin

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.enums.inventory_offset import InventoryOffset
from models.party_inventory import PartyInventory
from models.spell_type import SpellType

from services.sfx_library_service import SfxLibraryService
from services.world_clock import WorldClock

class GeneralSpellController(LoggerMixin):

    party_agent: PartyAgent
    world_clock: WorldClock
    sfx_library_service: SfxLibraryService
    party_inventory: PartyInventory

    def cast(self, spell_caster: PartyMemberAgent, spell_type: SpellType) -> bool:

        self.sfx_library_service.cast_spell_normal()

        # LEVEL ONE
        if spell_type.spell_key == "il":
            self.party_agent.set_light(radius = 3, expiry = self.world_clock.get_natural_time() + timedelta(hours = 4))

        elif spell_type.spell_key == "ixm":
            extra_food = random.randint(1, 6)
            self.party_inventory.safe_add(InventoryOffset.FOOD, extra_food)

        # LEVEL TWO
        else:
            assert False, f"Unknown spell_key={spell_type.spell_key} for {__class__.__name__}"

        return True