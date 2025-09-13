# file: maps/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .overworld import load_britannia
from .underworld import load_underworld

from maps import DataOVL, LocationLoader, LocationMetadataBuilder

def compose(provider: ServiceProvider):
    provider.register_instance(DataOVL.load())
    provider.register_instance(load_britannia())
    provider.register_instance(load_underworld())

    provider.register(LocationLoader)
    provider.register(LocationMetadataBuilder)
    


