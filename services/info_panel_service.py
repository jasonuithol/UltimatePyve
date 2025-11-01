import pygame

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.enums.ega_palette_values import EgaPaletteValues

from services.font_mapper import FontMapper
from services.info_panel_data_provider import EquipableItemsData, InfoPanelDataProvider, PartySummaryData
from services.input_service import InputService

from view.info_panel import ORIGINAL_PANEL_WIDTH, InfoPanel, InfoPanelDataSet
from view.main_display import MainDisplay

class InfoPanelService(DarkEventListenerMixin, LoggerMixin):
    
    info_panel:      InfoPanel
    party_agent:     PartyAgent
    global_registry: GlobalRegistry
    font_mapper:     FontMapper
    main_display:    MainDisplay
    input_service: InputService
    info_panel_data_provider: InfoPanelDataProvider

    def init(self):
        super().__init__()
        self._up_arrow   = self.font_mapper.map_code("IBM.CH", 24)
        self._down_arrow = self.font_mapper.map_code("IBM.CH", 25)

        black = self.global_registry.colors.get(EgaPaletteValues.Black)
        self._both_arrow = self._up_arrow.overlay_with(self._down_arrow, black)

    #
    # TODO: do we incur the cost of a render loop ?
    #
    def update_party_summary(self):
        data = self.info_panel_data_provider.get_party_summary_data()
        self.show_party_summary(data)

    def show_party_summary(self, party_summary_data: PartySummaryData, select_mode: bool = False):

        self._set_panel_geometry(split = True)

        if select_mode:
            self.info_panel.set_panel_title("Select:")
        else:
            self.info_panel.set_panel_title(None)

        # Party members
        self.info_panel.set_glyph_rows_top(party_summary_data.party_data_set)

        # Food, Gold, Current Date

        t = party_summary_data.datetime_

        food = f"F:{party_summary_data.food}"
        gold = f"G:{party_summary_data.gold}".rjust(ORIGINAL_PANEL_WIDTH - len(food))
        date = f"    {t.month}-{t.day}-{t.year}"

        bottom_glyph_rows = [
            self.font_mapper.map_ascii_string(food + gold),
            self.font_mapper.map_ascii_string(date)
        ]

        self.info_panel.set_glyph_rows_bottom(bottom_glyph_rows)

    def show_equipable_items(self, equipable_items_data: EquipableItemsData):

        self._set_panel_geometry(scroll = True)

        view_height = self.info_panel.get_viewable_size().h
        item_count = len(equipable_items_data.equipable_items_data_set)

        self.info_panel.set_panel_title(equipable_items_data.party_member_name)
        self.info_panel.set_glyph_rows_top(equipable_items_data.equipable_items_data_set[:min(view_height, item_count)])

    def choose_item(self, glyph_rows: InfoPanelDataSet, selected_index: int) -> int:

        # The data index of the highlight cursor
        item_count = len(glyph_rows)

        self._update_choose_item_display(glyph_rows, selected_index)

        while not self._has_quit:
            event = self.input_service.get_next_event()

            if event.key == pygame.K_UP:
                selected_index = (selected_index - 1) % item_count

            elif event.key == pygame.K_DOWN:
                selected_index = (selected_index + 1) % item_count

            elif event.key == pygame.K_RETURN:
                # Pressing enter will return the chosen item index.
                self.info_panel.set_highlighted_item(None)
                return selected_index

            elif event.key == pygame.K_ESCAPE:
                # pressing escape will cancel the action
                self.info_panel.set_highlighted_item(None)
                return None

            # Update the info_panel state
            self._update_choose_item_display(glyph_rows, selected_index)

    def _update_choose_item_display(self, glyph_rows: InfoPanelDataSet, selected_index: int):
        
        view_height = self.info_panel.get_viewable_size().h
        item_count = len(glyph_rows)

        # Middle row index within the viewport
        mid = view_height // 2

        # Try to center the selected index
        start_index = selected_index - mid

        # Clamp to valid range
        if start_index < 0:
            start_index = 0
        if start_index + view_height > item_count:
            start_index = max(item_count - view_height, 0)

        finish_index = start_index + view_height

        viewable_glyphs = glyph_rows[start_index:finish_index]
        self.info_panel.set_glyph_rows_top(viewable_glyphs)

        highlighted_index = selected_index - start_index
        self.info_panel.set_highlighted_item(highlighted_index)

        up = down = False
        if start_index > 0:
            up = True
        if finish_index < item_count:
            down = True

        self.log(
            f"DEBUG: up={up}, down={down}, highlighted_index={highlighted_index}, start_index={start_index},"
            +
            f" finish_index={finish_index}, view_height={view_height}, item_count={item_count}"
        )

        if   up and not down:   arrow = self._up_arrow
        elif down and not up:   arrow = self._down_arrow
        elif up and down:       arrow = self._both_arrow
        else:                   arrow = None

        self.info_panel.set_bottom_status_icon(arrow)

    def _set_panel_geometry(self, split = False, scroll = False):
        self.info_panel.set_panel_geometry(split = split, scroll = scroll)
        self.main_display.set_info_panel_split_state(split = split)



