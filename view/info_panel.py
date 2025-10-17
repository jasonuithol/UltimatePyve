from typing import Iterable
from dark_libraries.dark_math import Coord, Vector2

from data.global_registry import GlobalRegistry

from models.agents.party_agent        import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent

from models.u5_glyph import U5Glyph
from services.font_mapper import FontMapper
from view.display_config      import DisplayConfig
from view.scalable_component  import ScalableComponent

MAXIMUM_NAME_LENGTH = 8

RUNE_HELMET = 1
RUNE_SHIELD = 2
RUNE_ARMOUR = 3

class InfoPanel(ScalableComponent):

    display_config:  DisplayConfig
    global_registry: GlobalRegistry
    party_agent:     PartyAgent
    font_mapper:     FontMapper

    def __init__(self):
        pass

    def _after_inject(self):
        super().__init__(self.display_config.INFO_PANEL_SIZE * self.display_config.FONT_SIZE, self.display_config.SCALE_FACTOR)
        super()._after_inject()

    # This ignores all cursor state and just plasters the glyphs at the given coord.
    # It will not wrap, scroll, or update any state.
    def _print_glyphs_at(self, glyphs: Iterable[U5Glyph], char_coord: Coord):
        target = self.get_input_surface()
        for glyph in glyphs:
            glyph.blit_to_surface(char_coord, target)
            char_coord = char_coord + Vector2(1, 0)

    def _draw_player_slot(self, party_member_agent: PartyMemberAgent, char_coords: Coord):
        '''
        # Player Icon
        icon = self.global_registry.tiles.get(party_member_agent.tile_id)
        assert icon, f"No icon found for {party_member_agent.tile_id}"
        icon_offset = (char_offset * self.display_config.FONT_SIZE) + Vector2(2, 0)
        icon.blit_to_surface(self.get_input_surface(), icon_offset)
        '''

        # First row of text
        name_part   = party_member_agent.name
        health_part = str(party_member_agent.hitpoints) + party_member_agent._character_record.status

        if party_member_agent.maximum_mana == 0:
            mana_part = ""
        else:
            mana_part = str(party_member_agent._character_record.current_mp) + "M"

        composed_string = (
            name_part.ljust(MAXIMUM_NAME_LENGTH)
            + " " + 
            health_part.rjust(4)
            + " " + 
            mana_part.rjust(3)
        )

        first_row_glyphs = self.font_mapper.map_ascii_string(composed_string)
        self._print_glyphs_at(first_row_glyphs, char_coords)

        '''
        # Second row of text
        second_row = [0, RUNE_HELMET, RUNE_ARMOUR, RUNE_SHIELD] + [weapon.rune_id.value for weapon in party_member_agent.get_weapons() if not weapon.rune_id is None]
        second_row_glyphs = self.font_mapper.map_rune_codes(second_row)
        self._print_glyphs_at(second_row_glyphs, char_offset + Vector2(2, 1))
        '''


    def draw(self):
        # Try to keep this list arranged as the shape the slots are arranged.  Ta.
        slot_offsets = [
            (0,0), 
            (0,1),
            (0,2),
            (0,3),
            (0,4),
            (0,5)
        ]

        for party_member_index, party_member in enumerate(self.party_agent.get_party_members()):
            x, y = slot_offsets[party_member_index]
            self._draw_player_slot(party_member, Coord(x, y))
