import pygame
from models.agents.party_member_agent import PartyMemberAgent
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.main_loop_service import MainLoopService


class ReadyController:

    display_service: DisplayService
    main_loop_service: MainLoopService
    console_service: ConsoleService

    def handle_event(self, event: pygame.event.Event):
        if event.key == pygame.K_r:
            self.ready()

    def ready(self):
        self.console_service.print_ascii("Ready...")
        chosen_party_member_index = self.main_loop_service.choose_party_member()

        