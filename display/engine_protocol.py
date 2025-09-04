from typing import Protocol

from animation import sprite
from game.world_state import WorldState

class EngineProtocol(Protocol):
    world_state: WorldState
    def register_sprite(self, sprite_copy: sprite.Sprite) -> None:
        ...

