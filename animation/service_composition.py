# file: animation/service_composition.py
from animation.flame_sprite_factory import FlameSpriteFactory
from dark_libraries.service_provider import ServiceProvider

from animation.animated_tile_factory import AnimatedTileFactory
from animation.avatar_sprite_factory import AvatarSpriteFactory
from animation.sprite_registry import SpriteRegistry

def compose(provider: ServiceProvider):
    provider.register(SpriteRegistry)
    provider.register(AnimatedTileFactory)
    provider.register(FlameSpriteFactory)
    provider.register(AvatarSpriteFactory)

