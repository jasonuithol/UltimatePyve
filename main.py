from pathlib import Path
import colorama
import sys

from configure import get_u5_path, check_python_version
from dark_libraries.dark_socket_network import LISTENER_PORT, get_machine_address
from services.multiplayer_service import MultiplayerService

check_python_version()

from controllers.party_controller import PartyController
# Makes best effort to turn on ANSI support for console error messages.
# Warning: Activates colorize in python 3.13+.  If you don't like it, set environment variable PYTHON_COLORS=0
# Or if you don't like the colors themselves, change the defaults in your terminal.
# Or, add a config file (unfortunately, regexp based) (see https://github.com/magmax/colorize/blob/master/.colorize.conf)
colorama.init()

# 3rd party messages will stand out (i.e. pygame, package deprecation warnings.)
print(colorama.Fore.CYAN)

u5_path: Path = get_u5_path()

print(f"(main) Found legal copy of Ultima V at '{u5_path}'")

# Set up pygame
import gc
import pygame

from dark_libraries.service_provider import ServiceProvider
from service_composition import compose

from controllers.initialisation_controller import InitialisationController

pygame.init()

provider = ServiceProvider()

compose(provider)
print("(main) Service provider registration finished.")

provider.inject_all()
print("(main) Service provider injection finished.")

init: InitialisationController = provider.resolve(InitialisationController)
init.init(u5_path)

# finished initialising, tidy up.
gc.collect()

multiplayer_service: MultiplayerService = provider.resolve(MultiplayerService)
if "-host" in sys.argv:
    multiplayer_service.start_hosting()
if "-join" in sys.argv:
    ip_address = get_machine_address()
    multiplayer_service.connect_to_host(ip_address, LISTENER_PORT)


pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
pygame.mixer.init()

party_controller: PartyController = provider.resolve(PartyController)
party_controller.run()



