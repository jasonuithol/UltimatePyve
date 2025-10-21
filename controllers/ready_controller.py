import pygame

from data.global_registry import GlobalRegistry
from models.agents.party_agent import PartyAgent

from services.console_service import ConsoleService
from services.font_mapper import FontMapper
from services.info_panel_service import InfoPanelService
from services.main_loop_service import MainLoopService

class ReadyController:

    main_loop_service: MainLoopService
    console_service: ConsoleService
    party_agent: PartyAgent
    info_panel_service: InfoPanelService
    global_registry: GlobalRegistry
    font_mapper: FontMapper

    def handle_event(self, event: pygame.event.Event):
        if event.key == pygame.K_r:
            self.ready()

    def ready(self):

        #
        # Step 1: Choose player
        #

        self.console_service.print_ascii("Ready...")
        self.console_service.print_ascii("Player: ", include_carriage_return = False)

        selected_member_index = self.main_loop_service.choose_item(
            item_count = self.party_agent.get_party_count()
        )

        if selected_member_index is None:
            self.console_service.print_ascii("None")
            return

        party_member_agent = self.party_agent.get_party_member(selected_member_index)
        self.console_service.print_ascii(party_member_agent.name + " !")

        #
        # Step 2: Choose Item
        #

        item_id_indexes = self.info_panel_service.show_equipable_items(selected_member_index, 0)

        selected_item_index = self.main_loop_service.choose_item(
            len(item_id_indexes)
        )

        selected_item = self.global_registry.item_types.get(item_id_indexes[selected_item_index])

        self.console_service.print_ascii(f"Item {selected_item.name} chosen")

        self.info_panel_service.show_party_summary()


      

