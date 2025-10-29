import random

from dark_libraries.dark_math import Vector2
from dark_libraries.logging import LoggerMixin

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.spell_type import SpellType
from services.main_loop_service import MainLoopService
from services.npc_service import NpcService
from models.enums.direction_map import DIRECTION_SECTORS

class DirectionalSpellController(LoggerMixin):

    party_agent: PartyAgent
    main_loop_service: MainLoopService
    npc_service: NpcService

    def cast(self, spell_caster: PartyMemberAgent, spell_type: SpellType, direction: Vector2[int]) -> bool:

        # LEVEL ONE

        min_normal, max_normal = DIRECTION_SECTORS[direction]

        assert min_normal < max_normal, "Normals must be in increasing order of radian value."

        if spell_type.spell_key == "rh":
            #
            # TODO: Actually change the direction of the wind
            #
            pass

        # LEVEL FIVE

        elif spell_type.spell_key == "iz":

            monsters = self.npc_service.get_monsters()
            
            in_range_monsters = [
                m
                for m in monsters
                if min_normal <= spell_caster.coord.normal(m.coord) <= max_normal
            ]

            affected_monsters = [
                m
                for m in in_range_monsters
                if random.randint(30) < spell_caster.intelligence
            ]

            # apply the effect.  in this case - sleep
            for m in affected_monsters:
                #
                # TODO: This doesn't do anything right now
                #
                m.slept = True

        else:
            assert False, f"Unknown spell_key={spell_type.spell_key} for {__class__.__name__}"

