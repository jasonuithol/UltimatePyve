# file: game/interactable.py

from enum import Enum
from typing import Any, Protocol, Self
from dark_libraries import Coord
from dark_libraries.custom_decorators import immutable

class ActionType(Enum):
    MOVE_INTO   = 'move_into'
    OPEN        = 'open'    
    SEARCH      = 'search'
    GET         = 'get'
    JIMMY       = 'jimmy'

    BLOCKED     = 'blocked'
    LOCKED      = 'locked'
    KEY_BROKE   = 'key_broke'
    UNLOCKED    = 'unlocked'
    NO_KEYS     = 'no_keys'

    def to_action(self, action_parameters: dict[str, Any] = {}) -> 'Action':
        return Action(self, action_parameters)

    def execute(self, target: 'Interactable') -> Self:
        return self.to_action().execute(target)

    def get_action_type(self) -> Self:
        return self

@immutable
class Action:

    def __init__(self, action_type: ActionType, action_parameters: dict[str, Any] = {}):
        self.action_type = action_type
        self.action_parameters = action_parameters

    def execute(self, target: 'Interactable') -> Self:
        func = getattr(target, self.action_type.value)
        result: Action | ActionType = func(target, **self.action_parameters)
        if isinstance(result, ActionType):
            result = result.to_action()
        if "msg" in result.action_parameters:
            print(result.action_parameters["msg"])
        return result

    def to_action(self) -> Self:
        return self
    
    def get_action_type(self) -> ActionType:
        return self.action_type

class Interactable(Protocol):
    coord: Coord
    tile_id: int

    '''
    def create_sprite(self) -> Sprite:
        ...
    '''


    '''
    # Please do not override this function unless you know what you're doing.
    def receive_action(self, action: Action, actor=None) -> Action:
        func = getattr(self, action.action_name)
        resultant_action = func(self, **action.action_parameters)
        return resultant_action
    '''

    # For Viewport.draw_map
    def get_current_tile_id(self) -> int:
        ...

    # For main.run
    def pass_time(self):
        pass

    #
    # ACTION IMPLEMENTORS
    #

    def move_into(self, actor=None) -> Action:
        return None

    def open(self, actor=None) -> Action:
        return None

    def search(self, actor=None) -> Action:
        return None

    def get(self, actor=None) -> Action:
        return None

    '''
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
    '''


