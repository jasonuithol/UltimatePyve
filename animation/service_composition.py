# file: animation/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .animated_tile_factory import AnimatedTileFactory
from .avatar_sprite_factory import AvatarSpriteFactory
from .flame_sprite_factory import FlameSpriteFactory
from .sprite_registry import SpriteRegistry

def compose(provider: ServiceProvider):
    provider.register(SpriteRegistry)
    provider.register(AnimatedTileFactory)
    provider.register(FlameSpriteFactory)
    provider.register(AvatarSpriteFactory)

