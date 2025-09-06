# file: loaders/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from loaders.data import DataOVL
from loaders.location import LocationLoader, LocationMetadataBuilder
from loaders.overworld import load_britannia
from loaders.tileset import _ega_palette, load_tileset
from loaders.underworld import load_underworld

def compose(provider: ServiceProvider):
    provider.register_instance(DataOVL.load())
    provider.register_instance(_ega_palette)
    provider.register_instance(load_tileset())
    provider.register_instance(load_britannia())
    provider.register_instance(load_underworld())

    provider.register(LocationLoader)
    provider.register(LocationMetadataBuilder)
    


