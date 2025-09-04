from dark_libraries.service_provider import ServiceProvider

import loaders.service_composition

def compose(provider: ServiceProvider):
    loaders.service_composition.compose(provider)
