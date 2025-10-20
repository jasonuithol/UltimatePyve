from typing import Iterable
from dark_libraries.dark_math import Coord, Vector2

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.saved_game import SavedGame
from models.u5_glyph import U5Glyph

from services.font_mapper import FontMapper

from services.world_clock import WorldClock
from view.border_drawer import BorderDrawer
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
    world_clock:     WorldClock

    split_info_panel: bool = True

    def __init__(self):
        self._highlighted_party_member_index = None
        self._invisible_width = 15

    def set_highlighted_member(self, highlighted_party_member_index):
        self._highlighted_party_member_index = highlighted_party_member_index
        
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

    def _draw_player_slot(self, party_member_index: int):

        party_member_agent = self.party_agent.get_party_member(party_member_index)

        # First row of text
        name_part   = party_member_agent.name
        health_part = str(party_member_agent.hitpoints) + party_member_agent._character_record.status

        composed_string = (
            name_part.ljust(MAXIMUM_NAME_LENGTH)
            # make some room for the active party member arrow
            + "   " + 
            health_part.rjust(4)
        )

        first_row_glyphs = self.font_mapper.map_ascii_string(composed_string)
        right_arrow = self.global_registry.font_glyphs.get(("IBM.CH", 26))

        if party_member_index == self._highlighted_party_member_index:
            # Invert colors.
            first_row_glyphs = [glyph.invert_colors() for glyph in first_row_glyphs]
            right_arrow = right_arrow.invert_colors()

        char_coords = Coord(0, party_member_index)
        self._print_glyphs_at(first_row_glyphs, char_coords)

        if party_member_index == self.party_agent.get_active_member_index():
            self._print_glyphs_at([right_arrow], char_coords + (MAXIMUM_NAME_LENGTH + 1, 0))

    def _draw_food_gold_summary(self):
        first_row_y = 7
        food = f"F:{self.global_registry.saved_game.food[0]()}"
        gold = f"G:{self.global_registry.saved_game.gold[0]()}".rjust(self._invisible_width - len(food))

        first_row_glyphs = self.font_mapper.map_ascii_string(food + gold)
        self._print_glyphs_at(first_row_glyphs, Coord(0, first_row_y))
        
        t = self.world_clock.daylight_savings_time
        date = f"    {t.month}-{t.day}-{t.year}"

        second_row_glyphs = self.font_mapper.map_ascii_string(date)
        self._print_glyphs_at(second_row_glyphs, Coord(0, first_row_y + 1))

    def draw(self):
        for party_member_index in range(self.party_agent.get_party_count()):
            self._draw_player_slot(party_member_index)

        drawer = BorderDrawer(self.global_registry.blue_border_glyphs, self.get_input_surface())
        x_range_middle_to_right = list(range(self.display_config.INFO_PANEL_SIZE.w))
        y = self.display_config.INFO_PANEL_SIZE.h - 1

        # the glyph is vertical, the line is horizontal
        drawer.vertical(x_range_middle_to_right, y) 

        if self.split_info_panel:
            drawer.vertical(x_range_middle_to_right, y - 3)
            self._draw_food_gold_summary()

        

#        drawer.right(0, [y])
#        drawer.junction(self.display_config.INFO_PANEL_SIZE.w,  y)

