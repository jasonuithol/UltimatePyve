import colorama
# Makes best effort to turn on ANSI support for console error messages.
# Warning: Activates colorize in python 3.13+.  If you don't like it, set environment variable PYTHON_COLORS=0
# Or if you don't like the colors themselves, change the defaults in your terminal.
# Or, add a config file (unfortunately, regexp based) (see https://github.com/magmax/colorize/blob/master/.colorize.conf)
colorama.init()

# 3rd party messages will stand out (i.e. pygame, package deprecation warnings.)
print(colorama.Fore.CYAN)

# Set up pygame
import gc
import pygame

from dark_libraries.service_provider import ServiceProvider
from service_composition import compose

from controllers.initialisation_controller import InitialisationController
from controllers.main_loop_controller import MainLoopController

pygame.init()

provider = ServiceProvider()

compose(provider)
print("(main) Service provider registration finished.")

provider.inject_all()
print("(main) Service provider injection finished.")

init: InitialisationController = provider.resolve(InitialisationController)
init.init()

# finished initialising, tidy up.
gc.collect()

pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
pygame.mixer.init()

main: MainLoopController = provider.resolve(MainLoopController)
main.run()