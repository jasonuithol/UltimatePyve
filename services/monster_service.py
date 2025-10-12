import random
from typing import Iterable

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from data.global_registry import GlobalRegistry
from models.global_location import GlobalLocation

from services.console_service              import ConsoleService
from services.npc_service                  import NpcService
from services.map_cache.map_cache_service  import MapCacheService

class MonsterService(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    console_service:   ConsoleService
    map_cache_service: MapCacheService
    npc_service:       NpcService
    global_registry:   GlobalRegistry

    def __init__(self):
        super().__init__()        
        self._set_party_location(party_location = None)

    def _set_party_location(self, party_location: GlobalLocation):
        self._party_location = party_location
        if party_location is None:
            return
        self._current_map = self.global_registry.maps.get(party_location.location_index)
        self._current_boundary_rect = self._current_map.get_size() if self._current_map.location_index != 0 else None

    def _move_generator(self, monster_coord: Coord) -> Iterable[Coord]:

        # First of all, try the obvious move.
        yield monster_coord + monster_coord.normal_4way(self._party_location.coord)

        # OK, strike out in a random direction then
        alternative_moves = monster_coord.get_4way_neighbours()
        random.shuffle(alternative_moves)
        yield from alternative_moves

    def _find_next_move(self, blocked_coords: set[Coord], monster_coord: Coord) -> Coord:
     
        for target_coord in self._move_generator(monster_coord):
            out_of_bounds = (not self._current_boundary_rect is None) and self._current_boundary_rect.is_in_bounds(target_coord)
            if (not target_coord in blocked_coords) and (not out_of_bounds):
                return target_coord

        return None

    def _move(self, blocked_coords: set[Coord], monster_location: GlobalLocation) -> GlobalLocation:
        next_monster_coord = self._find_next_move(blocked_coords, monster_location.coord)
        if next_monster_coord is None:
            self.log(f"Unable to move from {monster_location.coord}")
            return None
        assert monster_location.coord.taxi_distance(next_monster_coord) == 1, f"Cannot move directly from {monster_location.coord} to {next_monster_coord}"
        self.log(f"DEBUG: Moving from {monster_location.coord} to {next_monster_coord}")
        return monster_location.move_to_coord(next_monster_coord)
    
    # TODO: what do we need this for ?
    def loaded(self, party_location: GlobalLocation):
        self._set_party_location(party_location)

    def pass_time(self, party_location: GlobalLocation):
        self._set_party_location(party_location)

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
                if self.npc_service.get_attacking_npc() is None:
                    self.npc_service.set_attacking_npc(npc)
            else:
                move_coord = self._move(blocked_coords.union(occupied_coords), npc.global_location)
                if not move_coord is None:
                    npc.global_location = move_coord

            new_coord = npc.get_coord()

            if old_coord != new_coord:
                occupied_coords.add(new_coord)
                occupied_coords.remove(old_coord)

