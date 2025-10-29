import pygame

from models.agents.party_agent import PartyAgent
from services.console_service import ConsoleService
from services.input_service import InputService

active_player_keymap = {
    pygame.K_1 : 0,
    pygame.K_2 : 1,
    pygame.K_3 : 2,
    pygame.K_4 : 3,
    pygame.K_5 : 4,
    pygame.K_6 : 5
}

class ActiveMemberController:

    party_agent: PartyAgent
    console_service: ConsoleService
    input_service: InputService

    # This never passes time or consumes items or nuffin
    def handle_event(self, event: pygame.event.Event):
        if event.key == pygame.K_0:
            self.party_agent.set_active_member(None)
            self.console_service.print_ascii(f"Set active player: None !")

        active_member_index = active_player_keymap.get(event.key, None)

        if active_member_index is None:
            return
        
        self.party_agent.set_active_member(active_member_index)
        self.console_service.print_ascii(f"Set active player: {self.party_agent.get_active_member().name} !")
