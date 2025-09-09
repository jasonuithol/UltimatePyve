# file: game/interactable.py

from typing import Protocol
from dark_libraries import Coord
from .interaction_result import InteractionResult

class Interactable(Protocol):
    coord: Coord
    tile_id: int

    '''
    def create_sprite(self) -> Sprite:
        ...
    '''


    def get_current_tile_id(self) -> int:
        ...

    def pass_time(self):
        return InteractionResult.nothing()

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


