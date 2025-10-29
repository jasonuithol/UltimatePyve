import random

from dark_libraries.dark_math import Vector2
from dark_libraries.logging import LoggerMixin

from models.agents.monster_agent import MonsterAgent
from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.spell_type import SpellType
from services.main_loop_service import MainLoopService
from services.npc_service import NpcService
from models.enums.direction_map import DIRECTION_SECTORS
from services.sfx_library_service import SfxLibraryService

class DirectionalSpellController(LoggerMixin):

    party_agent: PartyAgent
    main_loop_service: MainLoopService
    npc_service: NpcService
    sfx_library_service: SfxLibraryService

    def cast(self, spell_caster: PartyMemberAgent, spell_type: SpellType, direction: Vector2[int]) -> bool:

        affected_monsters = self._get_affected_monsters(spell_caster, direction)

        # LEVEL ONE

        if spell_type.spell_key == "rh":
            #
            # TODO: Actually change the direction of the wind
            #
            pass

        # LEVEL FIVE

        elif spell_type.spell_key == "iz":

            # apply the effect.  in this case - sleep
            for m in affected_monsters:
                #
                # TODO: This doesn't do anything right now
                #
                m.sleep()
                self.sfx_library_service.damage(m.coord)

        # LEVEL SIX

        else:
            assert False, f"Unknown spell_key={spell_type.spell_key} for {__class__.__name__}"


    def _get_affected_monsters(self, spell_caster: PartyMemberAgent, direction: Vector2[int]) -> set[MonsterAgent]:

        min_normal, max_normal = DIRECTION_SECTORS[direction]

        assert min_normal < max_normal, "Normals must be in increasing order of radian value."
            
        monsters = self.npc_service.get_monsters()

        in_range_monsters = {
            m
            for m in monsters
            if min_normal <= spell_caster.coord.normal(m.coord) <= max_normal
        }

        affected_monsters = {
            m
            for m in in_range_monsters
            if random.randint(0,30) < spell_caster.intelligence
        }

        return affected_monsters