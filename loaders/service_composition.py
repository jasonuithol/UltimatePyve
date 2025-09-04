from dark_libraries.service_provider import ServiceProvider

from loaders.data import DataOVL
from loaders.overworld import load_britannia
from loaders.tileset import _ega_palette, load_tileset
from loaders.underworld import load_underworld

def compose(provider: ServiceProvider):
    provider.register_singleton(DataOVL.load())
    provider.register_singleton(_ega_palette)
    provider.register_singleton(load_tileset())
    provider.register_singleton(load_britannia())
    provider.register_singleton(load_underworld())
