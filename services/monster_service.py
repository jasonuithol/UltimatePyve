import random
from typing import Iterable

from controllers.combat_controller import CombatController

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from models.npc_agent import NpcAgent
from models.global_location import GlobalLocation

from services.console_service             import ConsoleService
from services.map_cache.map_level_contents import MapLevelContents
from services.npc_service                 import NpcService
from services.map_cache.map_cache_service import MapCacheService

class MonsterService(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    console_service:   ConsoleService
    map_cache_service: MapCacheService
    npc_service:       NpcService
    combat_controller: CombatController

    def __init__(self):
        super().__init__()        
        self._party_location: GlobalLocation = None

    def _move_generator(self, monster_coord: Coord) -> Iterable[Coord]:

        # First of all, try the obvious move.
        yield monster_coord + monster_coord.normal_4way(self._party_location.coord)

        # OK, strike out in a random direction then
        alternative_moves = monster_coord.get_4way_neighbours()
        random.shuffle(alternative_moves)
        yield from alternative_moves

    def find_next_move(self, blocked_coords: set[Coord], monster_coord: Coord) -> Coord:

        map_level_contents: MapLevelContents = self.map_cache_service.get_map_level_contents(self._party_location.location_index, self._party_location.level_index)
        map_coords = set(map_level_contents._coord_contents_dict.keys())
     
        for move in self._move_generator(monster_coord):
            if (not move in blocked_coords) and move in map_coords:
                return move

        return None

    def _move(self, blocked_coords: set[Coord], monster_location: GlobalLocation) -> GlobalLocation:
        next_monster_coord = self.find_next_move(blocked_coords, monster_location.coord)
        if next_monster_coord is None:
            self.log(f"Unable to move from {monster_location.coord}")
            return None
        assert monster_location.coord.taxi_distance(next_monster_coord) == 1, f"Cannot move directly from {monster_location.coord} to {next_monster_coord}"
        self.log(f"DEBUG: Moving from {monster_location.coord} to {next_monster_coord}")
        return monster_location.move_to_coord(next_monster_coord)

    def _attack(self, npc_agent: NpcAgent):
        #
        # TODO: launch combat screen
        #
        self.console_service.print_ascii("Attacked !")
        self.combat_controller.enter_combat(npc_agent)

    def loaded(self, party_location: GlobalLocation):
        self._party_location = party_location

    def pass_time(self, party_location: GlobalLocation):

        self._party_location = party_location

        blocked_coords = self.map_cache_service.get_blocked_coords(
            self._party_location.location_index, 
            self._party_location.level_index, 
            transport_mode_index = 0
        )

        occupied_coords = self.npc_service.get_occupied_coords()

        # Give all the NPCs a turn.
        for npc in self.npc_service._active_npcs:
            old_coord = npc.get_coord()

            if npc.get_coord().taxi_distance(self._party_location.coord) == 1:
                self._attack(npc)
            else:
                move_coord = self._move(blocked_coords.union(occupied_coords), npc.global_location)
                if not move_coord is None:
                    npc.global_location = move_coord

            new_coord = npc.get_coord()

            if old_coord != new_coord:
                occupied_coords.add(new_coord)
                occupied_coords.remove(old_coord)

