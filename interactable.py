# file: interactable.py
from typing import Protocol
from custom_decorators import immutable
from dark_math import Coord
from sprite import Sprite

# Action results
R_QUIET_SUCCESS = ""
R_LOUD_SUCCESS  = "Success"

R_FAILED        = "Failed"
R_NOTHING_THERE = "Nothing to do"
R_KEYBROKE      = "Key broke"
R_LOCKED        = "Locked"

@immutable
class InteractionResult:
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message

    @classmethod
    def nothing(cls):
        return cls(success=False, message=R_NOTHING_THERE)

    @classmethod
    def result(cls, message: str):
        if message in [R_QUIET_SUCCESS, R_LOUD_SUCCESS]:
            return cls.ok(message)
        else:
            return cls.error(message)
        
    @classmethod
    def ok(cls, message=R_QUIET_SUCCESS):
        return cls(success=True, message=message)

    @classmethod
    def error(cls, message=R_FAILED):
        return cls(success=False, message=message)

class InteractableFactory(Protocol):
    def create_interactable(self, coord: Coord):
        ...

class Interactable(Protocol):
    coord: Coord
    tile_id: int

    def create_sprite(self) -> Sprite:
        ...

    def move_into(self, actor=None) -> InteractionResult:
        return InteractionResult.nothing()

    def jimmy(self, actor=None) -> InteractionResult:
        return InteractionResult.nothing()

    def yell_near(self, actor=None) -> InteractionResult:
        return InteractionResult.nothing()

    def look_at(self, actor=None) -> InteractionResult:
        return InteractionResult.nothing()

    def use_item_on(self, actor=None, item=None) -> InteractionResult:
        return InteractionResult.nothing()

    def cast_spell_on(self, actor=None, spell=None) -> InteractionResult:
        return InteractionResult.nothing()

    def attack(self, actor=None) -> InteractionResult:
        return InteractionResult.nothing()

