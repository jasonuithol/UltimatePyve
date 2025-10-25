# file: game/interactable.py

from typing import Protocol

from dark_libraries.dark_math import Coord
from models.move_into_result  import MoveIntoResult

class Interactable(Protocol):
    coord: Coord[int]
    tile_id: int

    # For Viewport.draw_map
    def get_current_tile_id(self) -> int:
        ...

    # For main.run
    def pass_time(self):
        pass

    #
    # ACTION IMPLEMENTORS
    #

    def move_into(self) -> MoveIntoResult:
        return MoveIntoResult(False, False)

    def open(self):
        return

    def search(self):
        return

    def get(self):
        return

    def jimmy(self):
        return

    '''

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
    '''


