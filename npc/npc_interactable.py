from dark_libraries.dark_math import Coord
from dark_libraries.service_provider import ServiceProvider

from animation.sprite import Sprite
from display.interactive_console import InteractiveConsole
from game.interactable.interactable import MoveIntoResult

from .npc_state import NpcState

# NOTE: Not a real interactable (YET)
class NpcInteractable:

    def __init__(self, tile_id: int, sprite: Sprite, npc_state: NpcState):
        self.tile_id = tile_id # ID of the first frame
        self.sprite = sprite
        self.npc_state = npc_state
        self.interactive_console: InteractiveConsole = ServiceProvider.get_provider().resolve(InteractiveConsole)

    def pass_time(self, blocked_coords: set[Coord], player_coord: Coord):
        self.npc_state.pass_time(blocked_coords, player_coord)

    def get_coord(self):
        return self.npc_state.global_location.coord

    #
    # ACTION IMPLEMENTORS
    #

    def move_into(self) -> MoveIntoResult:
        return MoveIntoResult(False, False)
    
    def attack(self):
        self.interactive_console.print_ascii("Attacking !")

    def cast_spell_on(self):
        pass