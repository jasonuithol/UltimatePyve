import random

from dark_libraries.dark_math import Coord, Vector2
from dark_libraries.logging import LoggerMixin

from models.agents.combat_agent import CombatAgent
from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.combat_map import CombatMap
from models.enums.ega_palette_values import EgaPaletteValues
from models.spell_type import SpellType
from models.enums.direction_map import DIRECTION_SECTORS

from services.console_service import ConsoleService
from services.input_service import InputService
from services.npc_service import NpcService
from services.sfx_library_service import SfxLibraryService
from services.view_port_service import ViewPortService

class DirectionalSpellController(LoggerMixin):

    party_agent: PartyAgent
    input_service: InputService
    npc_service: NpcService
    sfx_library_service: SfxLibraryService
    view_port_service: ViewPortService
    console_service: ConsoleService

    def cast(self, combat_map: CombatMap, spell_caster: PartyMemberAgent, spell_type: SpellType) -> bool:

        spell_direction = self.input_service.obtain_action_direction()
        if spell_direction is None:
            return False

        self.sfx_library_service.bubbling_of_reality()

        if combat_map:
            self.sfx_library_service.cone_of_magic(spell_caster.coord, spell_direction, EgaPaletteValues.Magenta, combat_map.get_size().to_rect(Coord(0,0)))

        self._apply_spell_effects(spell_caster, spell_type, spell_direction)
        
        if combat_map:
            self.view_port_service.set_magic_rays(None)

        return True

    def _apply_spell_effects(self, spell_caster: PartyMemberAgent, spell_type: SpellType, direction: Vector2[int]) -> bool:

        affected_npcs = self._get_affected_npcs(spell_caster, direction)

        # LEVEL ONE

        if spell_type.spell_key == "rh":
            #
            # TODO: Actually change the direction of the wind
            #
            self.console_service.print_ascii("TODO !")

        elif spell_type.spell_key == "ay":
            #
            # TODO: Actually make something vanish
            #
            self.console_service.print_ascii("TODO !")

        # LEVEL TWO

        elif spell_type.spell_key == "as":
            #
            # TODO: Unlock a trapped chest
            #
            self.console_service.print_ascii("TODO !")

        # LEVEL FIVE

        elif spell_type.spell_key == "iz":

            # apply the effect.  in this case - sleep
            for m in affected_npcs:
                m.sleep()
                self.sfx_library_service.damage(m.coord)

        # LEVEL SIX

        else:
            assert False, f"Unknown spell_key={spell_type.spell_key} for {__class__.__name__}"


    def _get_affected_npcs(self, spell_caster: PartyMemberAgent, direction: Vector2[int]) -> set[CombatAgent]:

        min_normal, max_normal = DIRECTION_SECTORS[direction]

        assert min_normal < max_normal, "Normals must be in increasing order of radian value."
            
        # Cannot cast a directional spell on yourself.            
        npcs = [npc for npc in self.npc_service.get_npcs().values() if npc != spell_caster]

        in_range_npcs = {
            m
            for m in npcs
            if min_normal <= spell_caster.coord.normal(m.coord) <= max_normal
        }

        affected_npcs = {
            m
            for m in in_range_npcs
            if random.randint(0,30) < spell_caster.intelligence
        }

        return affected_npcs