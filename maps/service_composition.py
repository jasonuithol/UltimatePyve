# file: maps/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from maps.u5map_loader import U5MapLoader

from .overworld import load_britannia
from .underworld import load_underworld

from maps import DataOVL, U5MapLoader, LocationMetadataBuilder, U5MapRegistry

def compose(provider: ServiceProvider):
    provider.register_instance(DataOVL.load())
    provider.register_instance(load_britannia())
    provider.register_instance(load_underworld())

    provider.register(U5MapLoader)
    provider.register(U5MapRegistry)
    provider.register(LocationMetadataBuilder)
    


