# file: maps/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .u5map_loader import U5MapLoader
from .data import DataOVL
from .u5map_loader import U5MapLoader
from .location_metadata_builder import LocationMetadataBuilder
from .u5map_registry import U5MapRegistry
from .overworld import load_britannia
from .underworld import load_underworld

def compose(provider: ServiceProvider):
    provider.register_instance(DataOVL.load())
    provider.register_instance(load_britannia())
    provider.register_instance(load_underworld())

    provider.register(U5MapLoader)
    provider.register(U5MapRegistry)
    provider.register(LocationMetadataBuilder)
    


