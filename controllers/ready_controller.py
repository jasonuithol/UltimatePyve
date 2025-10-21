import pygame

from data.global_registry import GlobalRegistry

from services.console_service import ConsoleService
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService

class ReadyController:

    console_service: ConsoleService
    info_panel_service: InfoPanelService
    global_registry: GlobalRegistry
    info_panel_data_provider: InfoPanelDataProvider

    def handle_event(self, event: pygame.event.Event):
        if event.key == pygame.K_r:
            self.ready()

    def ready(self):

        #
        # Step 1: Choose player
        #
        selected_member_index = self._step_1_choose_player()

        if selected_member_index is None:
            self.console_service.print_ascii("None")
            return

        #
        # Step 2: Choose Item
        #
        selected_item_id = self._step_2_choose_item(selected_member_index)
        selected_item = self.global_registry.item_types.get(selected_item_id)

        self.console_service.print_ascii(f"Item {selected_item.name} chosen")

        #
        # Step 3: Update inventories/equipped items
        #

        #
        # Step 4: Resume normal playing
        #
        self.info_panel_service.show_party_summary()

    def _step_1_choose_player(self) -> int:

        party_summary_data_set = self.info_panel_data_provider.get_party_summary_data()

        # QUASI-HEMI-OPTIONAL: Guarantee the correct starting state.
        self.info_panel_service.show_party_summary(party_summary_data_set)

        self.console_service.print_ascii("Ready...")
        self.console_service.print_ascii("Player: ", include_carriage_return = False)

        return self.info_panel_service.choose_item(party_summary_data_set.party_data_set)

    def _step_2_choose_item(self, selected_member_index: int) -> int:

        equipable_item_data = self.info_panel_data_provider.get_equipable_items_data(selected_member_index)
        self.console_service.print_ascii(equipable_item_data.party_member_name + " !")

        # ENTIRELY OPTIONAL
        self.info_panel_service.show_equipable_items(equipable_item_data)

        selected_item_index = self.info_panel_service.choose_item(equipable_item_data.equipable_items_data_set)
        return equipable_item_data.equipable_items_index_map[selected_item_index]
   

      

