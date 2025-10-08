import random

from dark_libraries.dark_math import Coord
from dark_libraries.service_provider import ServiceProvider

from models.u5_map import U5Map
from services.console_service import ConsoleService
from dark_libraries.logging import Logger
from models.global_location import GlobalLocation

from .npc_state import NpcState

class MonsterState(NpcState):

    def __init__(self, global_location: GlobalLocation):

        super().__init__(global_location)
        
        self.console_service: ConsoleService = ServiceProvider.get_provider().resolve(ConsoleService)
        self.logger = Logger(self)

    def find_next_move(self, blocked_coords: set[Coord], player_coord: Coord) -> Coord:

        u5map: U5Map = self.global_registry.maps.get(self.global_location.location_index)

        obvious_move = self.get_coord() + self.get_coord().normal_4way(player_coord)
        if (not obvious_move in blocked_coords) and u5map.size_in_tiles.is_in_bounds(obvious_move):
            return obvious_move

        alternative_moves = self.get_coord().get_4way_neighbours()
        random.shuffle(alternative_moves)
        for alternative_move in alternative_moves:
            if (not alternative_move in blocked_coords) and u5map.size_in_tiles.is_in_bounds(obvious_move):
                return alternative_move

        return None

    def _move(self, blocked_coords: set[Coord], player_coord: Coord):
        next_coord = self.find_next_move(blocked_coords, player_coord)
        if next_coord is None:
            self.logger.log(f"Unable to move from {self.get_coord()}")
            return
        assert self.get_coord().taxi_distance(next_coord) == 1, f"Cannot move directly from {self.get_coord()} to {next_coord}"
        self.logger.log(f"Moving from {self.get_coord()} to {next_coord}")
        self.global_location = GlobalLocation(
            self.global_location.location_index,
            self.global_location.level_index,
            next_coord
        )

    def _attack(self):
        #
        # TODO: launch combat screen
        #
        self.console_service.print_ascii("Attacked !")

    def take_turn(self, blocked_coords: set[Coord], player_coord: Coord):
        if self.get_coord().taxi_distance(player_coord) == 1:
            self._attack()
        else:
            self._move(blocked_coords, player_coord)

    def pass_time(self, blocked_coords: set[Coord], player_coord: Coord):
        self.take_turn(blocked_coords, player_coord)



# TODO: This needs to be burned to the ground and redone
'''
#
# MAIN
#

if __name__ == "__main__":

    #
    # TODO: We nuked most of the tests in the Monster pathing wars.  Redo.
    #

    class PlayerStateStub:
        def __init__(self, coord):
            self.coord = coord
        def get_current_position(self):
            return None, None, self.coord
        
    class InteractiveConsoleStub:
        def __init__(self):
            self.recorded_messages = []
        def print_ascii(self, msg):
            print(f"Received print_ascii msg={msg}")
            self.recorded_messages.append(msg)

    monster_location = GlobalLocation(0,0,(10,10))
    player_location = GlobalLocation(0,0,Coord(20,20))

    monster_state = object.__new__(MonsterState)
    monster_state.global_location = monster_location
    monster_state.console_service = InteractiveConsoleStub()

#    assert monster_state._get_player_coord() == player_coord, "Not obtaining correct player_coord."

    monster_state.pass_time()

    monster_state.pass_time()

    expected_num_coords = monster_state.coord.taxi_distance(player_coord) - 1

    for i in range(expected_num_coords + 1):
        monster_state.pass_time()
    assert "Attacked !" in monster_state.interactive_console.recorded_messages, "Did not attack"

    monster_state.coord = monster_coord
    monster_state.pass_time()

    player_coord = Coord(15,15)
    monster_state.player_state.coord = player_coord
    monster_state.pass_time()

    expected_num_coords = monster_state.coord.taxi_distance(player_coord) - 1

    player_coord = Coord(16,16)
    monster_state.player_state.coord = player_coord
    monster_state.pass_time()

    expected_num_coords = monster_state.coord.taxi_distance(player_coord) - 1

    print("All tests passed.")
    
'''