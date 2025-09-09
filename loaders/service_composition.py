# file: loaders/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .overworld import load_britannia
from .tileset import _ega_palette, load_tileset
from .underworld import load_underworld

from loaders import DataOVL, LocationLoader, LocationMetadataBuilder

def compose(provider: ServiceProvider):
    provider.register_instance(DataOVL.load())
    provider.register_instance(_ega_palette)
    provider.register_instance(load_tileset())
    provider.register_instance(load_britannia())
    provider.register_instance(load_underworld())

    provider.register(LocationLoader)
    provider.register(LocationMetadataBuilder)
    


