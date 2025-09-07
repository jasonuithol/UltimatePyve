# file: game/interactable.py
from typing import Optional, Protocol
from dark_libraries.custom_decorators import immutable
from dark_libraries.dark_math import Coord
from animation.sprite import Sprite

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

class InteractableState:
    def _after_inject(self):
        self.interactables: dict[Coord, Interactable] = dict()
        self.interactable_factories: dict[int, InteractableFactory] = dict()

    def register_interactable_factory(self, tile_id: int, factory: InteractableFactory) -> None:
        self.interactable_factories[tile_id] = factory

    def get_interactable(self, tile_id: int, coord: Coord) -> Optional[Interactable]:

        assert len(self.interactable_factories) > 0, "no interactable factories registered before we need them."

        # If there's already something at the co-ordinates, return that.
        interactable = self.interactables.get(coord, None)
        if interactable:
            return interactable
        
        # If this is a false alarm, bail.
        if not tile_id in self.interactable_factories.keys():
            return None
        
        # Create an interactable, store and return it.
        interactable = self.interactable_factories[tile_id].create_interactable(coord)
        self.interactables[coord] = interactable
        return interactable

    def clear_interactables(self) -> None:
        self.interactables.clear()    

