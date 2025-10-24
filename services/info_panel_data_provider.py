from datetime import datetime
from typing import Iterable

from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.enums.inventory_offset import InventoryOffset
from models.equipable_item_type import EquipableItemType

from models.glyph_key import GlyphKey
from services.font_mapper import FontMapper
from services.world_clock import WorldClock

from view.info_panel import MAXIMUM_NAME_LENGTH, InfoPanelDataRow, InfoPanelDataSet

class PartySummaryData:
    party_data_set: InfoPanelDataSet
    food: int
    gold: int
    datetime_: datetime

class EquipableItemsData:

    party_member_index: int
    party_member_name: str

    equipable_items_index_map: dict[int, int]
    equipable_items_data_set:  InfoPanelDataSet

class InfoPanelDataProvider(LoggerMixin):

    party_agent:     PartyAgent
    global_registry: GlobalRegistry
    font_mapper:     FontMapper
    world_clock:     WorldClock
    
    def get_party_summary_data(self) -> PartySummaryData:
        data = PartySummaryData()

        data.party_data_set = [
            self._build_player_slot(ix)
            for ix in range(self.party_agent.get_party_count())
        ]

        data.food = self.global_registry.saved_game.read_u16(InventoryOffset.FOOD.value)
        data.gold = self.global_registry.saved_game.read_u16(InventoryOffset.GOLD.value)
        data.datetime_ = self.world_clock.daylight_savings_time

        return data
    
    def _build_player_slot(self, party_member_index: int) -> InfoPanelDataRow:

        party_member_agent = self.party_agent.get_party_member(party_member_index)

        # First row of text
        name_part   = party_member_agent.name
        health_part = str(party_member_agent.hitpoints) + party_member_agent._character_record.status

        is_active = party_member_index == self.party_agent.get_active_member_index()
        active_member_indicator_glyph_code = 26 if is_active else 0

        glyph_row = (
            self.font_mapper.map_ascii_string(name_part.ljust(MAXIMUM_NAME_LENGTH + 1))
            +
            [self.global_registry.font_glyphs.get(GlyphKey("IBM.CH", active_member_indicator_glyph_code))]
            + 
            self.font_mapper.map_ascii_string(health_part.rjust(5))
        )

        return glyph_row
    
    def get_equipable_items_data(self, party_member_index: int) -> EquipableItemsData:

        party_member_agent = self.party_agent.get_party_member(party_member_index)
        tile_id_to_glyph_rows = dict(self._generate_equipable_items(party_member_index))

        data = EquipableItemsData()

        data.party_member_index = party_member_index
        data.party_member_name = party_member_agent.name

        data.equipable_items_index_map = {
            index : item_id
            for index, item_id in enumerate(tile_id_to_glyph_rows.keys())
        }

        data.equipable_items_data_set = [
            glyph_row
            for glyph_row in tile_id_to_glyph_rows.values()
        ]
        return data    
    
    def _generate_equipable_items(self, party_member_index: int) -> Iterable[tuple[int, InfoPanelDataRow]]:

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
                rune_glyph = self.global_registry.font_glyphs.get(GlyphKey("RUNES.CH", equipable_item_type.rune_id.value))
            else:
                rune_glyph = self.global_registry.font_glyphs.get(GlyphKey("RUNES.CH", 0))

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
