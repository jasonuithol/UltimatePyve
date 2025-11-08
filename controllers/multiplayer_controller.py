import pygame

from dark_libraries.dark_socket_network import LISTENER_PORT, get_machine_address
from services.console_service import ConsoleService
from services.input_service import InputService
from services.multiplayer_service import MultiplayerService

class MultiplayerController:

    # Injectable
    multiplayer_service: MultiplayerService
    console_service: ConsoleService
    input_service: InputService

    def handle_event(self, event: pygame.event.Event):

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_F1:
            self.host_server()
            self.input_service.discard_events()

        elif event.key == pygame.K_F2:
            self.join_server()
            self.input_service.discard_events()

    def host_server(self):
        if self.multiplayer_service.client:
            self.console_service.print_ascii(f"Leave current host first !")

        elif self.multiplayer_service.server:
            self.multiplayer_service.quit()
            self.console_service.print_ascii(f"Quit hosting")
        else:
            self.multiplayer_service.start_hosting()
            self.console_service.print_ascii(f"Hosting on {self.multiplayer_service.server.host}:{self.multiplayer_service.server.port}")

    def join_server(self):
        if self.multiplayer_service.server:
            self.console_service.print_ascii(f"Stop hosting first !")

        elif self.multiplayer_service.client:
            self.multiplayer_service.quit()
            self.console_service.print_ascii(f"Left server")
        else:
            ip_address = get_machine_address()
            try:
                self.multiplayer_service.connect_to_host(ip_address, LISTENER_PORT)
                self.console_service.print_ascii(f"Joined server on {ip_address}:{LISTENER_PORT}")
            except TimeoutError:
                self.console_service.print_ascii(f"No server at {ip_address}:{LISTENER_PORT} !")


