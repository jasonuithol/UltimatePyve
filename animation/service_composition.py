# file: animation/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from animation.sprite import AnimatedTileFactory, AvatarSpriteFactory

def compose(provider: ServiceProvider):
    provider.register(AnimatedTileFactory)
    provider.register(AvatarSpriteFactory)
