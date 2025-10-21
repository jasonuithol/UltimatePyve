from typing import Iterable
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.agents.party_agent import PartyAgent
from models.enums.inventory_offset import InventoryOffset
from models.equipable_items import EquipableItemType
from models.u5_glyph import U5Glyph
from services.font_mapper import FontMapper
from services.world_clock import WorldClock
from view.info_panel import MAXIMUM_NAME_LENGTH, ORIGINAL_PANEL_WIDTH, InfoPanel
from view.main_display import MainDisplay

class InfoPanelService(LoggerMixin):
    
    info_panel:      InfoPanel
    party_agent:     PartyAgent
    global_registry: GlobalRegistry
    font_mapper:     FontMapper
    world_clock:     WorldClock
    main_display:    MainDisplay

    def _set_panel_geometry(self, split = False, scroll = False):
        self.info_panel.set_panel_geometry(split = split, scroll = scroll)
        self.main_display.set_info_panel_split_state(split = split)

    def show_party_summary(self):
        self._set_panel_geometry(split = True)

        # Party members

        top_glyph_rows = [
            self._build_player_slot(ix)
            for ix in range(self.party_agent.get_party_count())
        ]
        self.info_panel.set_glyph_rows_top(top_glyph_rows)

        # Food, Gold, Current Date

        food = f"F:{self.global_registry.saved_game.read_u16(InventoryOffset.FOOD.value)}"
        gold = f"G:{self.global_registry.saved_game.read_u16(InventoryOffset.GOLD.value)}".rjust(ORIGINAL_PANEL_WIDTH - len(food))
        t = self.world_clock.daylight_savings_time
        date = f"    {t.month}-{t.day}-{t.year}"

        bottom_glyph_rows = [
            self.font_mapper.map_ascii_string(food + gold),
            self.font_mapper.map_ascii_string(date)
        ]

        self.info_panel.set_glyph_rows_bottom(bottom_glyph_rows)

    def show_equipable_items(self, party_member_index: int, scroll_offset: int) -> dict[int, int]:

        self._set_panel_geometry(scroll = True)

        party_member_agent = self.party_agent.get_party_member(party_member_index)
        self.info_panel.set_panel_title(party_member_agent.name)

        item_glyphstring_dict    = dict(self._generate_equipable_items(party_member_index))
        visible_glyphstring_dict = dict(list(item_glyphstring_dict.items())[scroll_offset : scroll_offset + 7])
        self.info_panel.set_glyph_rows_top(visible_glyphstring_dict.values())

        return {
            index : item_id   
            for index, item_id in enumerate(visible_glyphstring_dict.keys())
        }

    def _build_player_slot(self, party_member_index: int) -> Iterable[U5Glyph]:

        party_member_agent = self.party_agent.get_party_member(party_member_index)

        # First row of text
        name_part   = party_member_agent.name
        health_part = str(party_member_agent.hitpoints) + party_member_agent._character_record.status

        is_active = party_member_index == self.party_agent.get_active_member_index()
        active_member_indicator_glyph_code = 26 if is_active else 0

        glyph_row = (
            self.font_mapper.map_ascii_string(name_part.ljust(MAXIMUM_NAME_LENGTH + 1))
            +
            [self.global_registry.font_glyphs.get(("IBM.CH", active_member_indicator_glyph_code))]
            + 
            self.font_mapper.map_ascii_string(health_part.rjust(5))
        )

        return glyph_row
    
    def _generate_equipable_items(self, party_member_index: int) -> Iterable[tuple[int, Iterable[U5Glyph]]]:

        party_member = self.party_agent.get_party_member(party_member_index)
        items_equipped = party_member.get_equipped_items()
                            
        for item_id, equipable_item_type in self.global_registry.item_types.items():
            if not isinstance(equipable_item_type, EquipableItemType):
                continue
            quantity_held = self.global_registry.saved_game.read_u8(equipable_item_type.inventory_offset)
            is_equipped = (equipable_item_type in items_equipped)

            if not is_equipped and quantity_held == 0:
                continue

            if is_equipped and quantity_held == 0:
                prefix = "--"
            else:
                prefix = str(quantity_held).rjust(2) # this means we can only have 99 or less things of any type of thing.

            if is_equipped:
                assert not equipable_item_type.rune_id is None, "Must have a rune_id"
                rune_glyph = self.global_registry.font_glyphs.get(("RUNES.CH", equipable_item_type.rune_id.value))
            else:
                rune_glyph = self.global_registry.font_glyphs.get(("RUNES.CH", 0))

            assert not rune_glyph is None, f"Must have a rune_glyph (is_equipped={is_equipped}, rune_id={equipable_item_type.rune_id})"

            item_name = equipable_item_type.short_name
            if not item_name:
                item_name = equipable_item_type.name
            assert not item_name is None, "Must have an item_name"

            glyphs = (
                self.font_mapper.map_ascii_string(prefix)
                +
                [rune_glyph]
                +
                self.font_mapper.map_ascii_string(item_name)
            )

            yield item_id, glyphs        
