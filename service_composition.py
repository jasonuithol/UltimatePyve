# file: service_composition.py
from dark_libraries.service_provider import ServiceProvider

import loaders.service_composition
import display.service_composition
import game.service_composition
import animation.service_composition

def compose(provider: ServiceProvider):

    for module in [loaders, display, game, animation]:
        print(f"Pre-registering {module.__name__.upper()}")
        module.service_composition.compose(provider)

    print("Pre-registration COMPLETE")
    