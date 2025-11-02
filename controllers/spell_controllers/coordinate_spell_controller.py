import random

from dark_libraries.dark_math import Coord, Rect

from models.agents.combat_agent import CombatAgent
from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.combat_map import CombatMap
from models.enums.projectile_type import ProjectileType
from models.spell_type import SpellType

from services.input_service import InputService
from services.npc_service import NpcService
from services.sfx_library_service import SfxLibraryService

PROJECTILE_TYPES = {
    "gp"  : ProjectileType.MagicMissile,
    "kx"  : ProjectileType.MagicMissile,
    "izg" : ProjectileType.MagicMissile,

    "vf"  : ProjectileType.Fireball,
    "ing" : ProjectileType.Poison,
    "ifg" : ProjectileType.Fireball,
    
    "rxb" : ProjectileType.MagicMissile,
    "axe" : ProjectileType.MagicMissile,
    "xc"  : ProjectileType.MagicMissile
}

class CoordinateSpellController:

    party_agent:         PartyAgent
    input_service:       InputService
    npc_service:         NpcService
    sfx_library_service: SfxLibraryService

    def cast(self, combat_map: CombatMap, spell_caster: PartyMemberAgent, spell_type: SpellType) -> bool:

        assert combat_map, f"Should be in combat, or have been prevented from casting this spell: spell_key={spell_type.spell_key}"

        boundary_rect = combat_map.get_size().to_rect(Coord(0,0))

        spell_coord = self.input_service.obtain_cursor_position(
            starting_coord  = spell_caster.coord,
            boundary_rect   = boundary_rect,
            range_          = 255
        )

        if spell_coord is None:
            return False

        self.sfx_library_service.bubbling_of_reality()
        
        self._apply_spell_effect(spell_caster, spell_type, spell_coord, boundary_rect)

        return True

    def _apply_spell_effect(self, spell_caster: PartyMemberAgent, spell_type: SpellType, spell_coord: Coord[int], boundary_rect: Rect[int]) -> bool:

        target_npc: CombatAgent = self.npc_service.get_npc_at(spell_coord)
        if target_npc is None:
            to_hit = True
        else:
            #
            # TODO: We need better than this obviously
            #
            to_hit = random.randint(0, 100) < target_npc.armour * 3

        if not to_hit:
            actual_spell_coords = [
                coord
                for coord in spell_coord.get_8way_neighbours()
                if boundary_rect.is_in_bounds(coord)
            ]

            spell_coord = random.choice(actual_spell_coords)

        self.sfx_library_service.emit_projectile(ProjectileType.MagicMissile, spell_caster.coord, spell_coord)

        if spell_type.spell_key in ["gp", "vf"]:
            if to_hit and target_npc:
                #
                # TODO: We need better than this obviously
                #
                target_npc.hitpoints = max(0, target_npc.hitpoints - 5)
                self.sfx_library_service.damage(spell_coord)

