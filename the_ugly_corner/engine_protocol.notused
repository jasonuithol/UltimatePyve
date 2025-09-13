# file: display/engine_protocol.py
from typing import Protocol

from animation import sprite
from game.world_state import WorldState

class EngineProtocol(Protocol):

    # Hopefull injected !
    world_state: WorldState

    # Inheriting from Protocol means we get some weird shit happening with __init__.
    # Redefine it here.
    def __init__(self):
        object.__init__(self)

    def register_sprite(self, sprite_copy: sprite.Sprite) -> None:
        ...

