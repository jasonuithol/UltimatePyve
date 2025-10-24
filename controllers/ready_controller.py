import pygame

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.enums.equipable_item_slot import EquipableItemSlot
from models.equipable_item_type import EquipableItemType
from services.console_service import ConsoleService
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService

class ReadyController:

    console_service: ConsoleService
    global_registry: GlobalRegistry

    info_panel_service:       InfoPanelService
    info_panel_data_provider: InfoPanelDataProvider

    party_agent: PartyAgent

    def handle_event(self, event: pygame.event.Event):
        if event.key == pygame.K_r:
            self.ready()

    def ready(self):
        self._ready()

        # Restore previous info panel state.
        party_data = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_data)

    def _ready(self):

        self.selected_member_index = 0
        self.selected_item_index = 0

        #
        # Step 1: Choose player
        #
        self._choose_player()

        if self.selected_member_index is None:
            return

        #
        # Step 2: Choose Item to toggle
        #
        while True:

            # Set the info_panel into the correct state for phase 2
            equipable_item_data = self.info_panel_data_provider.get_equipable_items_data(self.selected_member_index)
            self.info_panel_service.show_equipable_items(equipable_item_data)

            self.console_service.print_ascii("Item: ", include_carriage_return = False)

            self.selected_item_index = self.info_panel_service.choose_item(
                glyph_rows = equipable_item_data.equipable_items_data_set,
                selected_index = self.selected_item_index
            )

            if self.selected_item_index is None:
                #
                # Exit
                #
                self.console_service.print_ascii("Done")
                return            

            selected_item_id = equipable_item_data.equipable_items_index_map[self.selected_item_index]

            #
            # Step 3: Update inventories/equipped items
            #
            self._update_inventories(selected_item_id)

    def _choose_player(self) -> int:

        self.console_service.print_ascii("Ready...", no_prompt = True)
        self.console_service.print_ascii("", no_prompt = True)
        self.console_service.print_ascii("Player: ", include_carriage_return = False)

        party_summary_data_set = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_summary_data_set, select_mode = True)
        self.selected_member_index = self.info_panel_service.choose_item(
            glyph_rows = party_summary_data_set.party_data_set,
            selected_index = self.selected_member_index
        )

        if self.selected_member_index is None:
            self.console_service.print_ascii("None")
        else:
            selected_member = self.party_agent.get_party_member(self.selected_member_index)
            self.console_service.print_ascii(selected_member.name, no_prompt = True)

    def _print_rejection(self, msg):
        self.console_service.print_ascii("",  no_prompt = True)
        self.console_service.print_ascii("",  no_prompt = True)
        self.console_service.print_ascii(msg, no_prompt = True)
        self.console_service.print_ascii("",  no_prompt = True)

    def _update_inventories(self, selected_item_id: int):

        selected_item: EquipableItemType = self.global_registry.item_types.get(selected_item_id)
        current_party_qty                = self.global_registry.saved_game.read_u8(selected_item.inventory_offset)
        party_member                     = self.party_agent.get_party_member(self.selected_member_index)

        if party_member.has_equipped_item(selected_item_id):
            # unequipping an item
            self.global_registry.saved_game.write_u8(selected_item.inventory_offset, current_party_qty + 1)
            party_member.unequip_item(selected_item_id)
            
        elif not party_member.is_slot_available(selected_item.slot) :
            if selected_item.slot == EquipableItemSlot.ONE_HAND:
                self._print_rejection("Thou must free one of thy hands first !")
            if selected_item.slot == EquipableItemSlot.TWO_HAND:
                self._print_rejection("Both hands must be free before thou canst wield that !")
            if selected_item.slot == EquipableItemSlot.HEAD:
                self._print_rejection("Remove first thy present helm !")
            if selected_item.slot == EquipableItemSlot.NECK:
                self._print_rejection("Thou must remove thine other amulet !")
            if selected_item.slot == EquipableItemSlot.BODY:
                self._print_rejection("Thou must first remove thine other armour !")
            if selected_item.slot == EquipableItemSlot.FINGER:
                self._print_rejection("Only one magic ring may be worn at a time !")

        elif not party_member.can_carry_extra_weight(selected_item):
            self._print_rejection("Thou art not strong enough !")

        else:
            # Equipping an item into an available slot
            assert current_party_qty > 0, f"No items of item_id={selected_item_id} in party inventory !"
            self.global_registry.saved_game.write_u8(selected_item.inventory_offset, current_party_qty - 1)
            party_member.equip_item(selected_item_id)


   

      

