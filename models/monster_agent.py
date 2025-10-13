import random
from typing import Iterable

from dark_libraries.dark_math import Coord, Rect
from dark_libraries.logging   import LoggerMixin

from models.npc_agent import NpcAgent

class MonsterAgent(NpcAgent, LoggerMixin):

    def _move_generator(self, target_coord: Coord) -> Iterable[Coord]:

        # First of all, try the obvious move.
        yield self.global_location.coord + self.global_location.coord.normal_4way(target_coord)

        # OK, strike out in a random direction then
        alternative_moves = self.global_location.coord.get_4way_neighbours()
        random.shuffle(alternative_moves)
        yield from alternative_moves

    def _find_next_move(self, 
                            target_coord:      Coord, 
                            forbidden_coords:  set[Coord],
                            boundary_rect:     Rect | None
                        ) -> Coord:
     
        for next_move_coord in self._move_generator(target_coord):

            is_forbidden      = next_move_coord in forbidden_coords
            is_in_outer_world = boundary_rect is None
            is_out_of_bounds  = (not boundary_rect is None) and (not boundary_rect.is_in_bounds(next_move_coord))

            if (not is_forbidden) and (is_in_outer_world or (not is_out_of_bounds)):
                return next_move_coord
            else:
                self.log(f"DEBUG: Rejecting proposed next_move_coord={next_move_coord} (is_forbidden={is_forbidden}, is_in_outer_world={is_in_outer_world}, is_out_of_bounds={is_out_of_bounds})")

        return None
    
    def move_towards(self, 
                        target_coord:      Coord, 
                        forbidden_coords:  set[Coord],
                        boundary_rect:     Rect
                     ):

        next_move_coord = self._find_next_move(
            target_coord,
            forbidden_coords, 
            boundary_rect 
        )

        if next_move_coord is None:
            self.log(f"Unable to move from {self.global_location.coord}")
            return None

        assert self.global_location.coord.taxi_distance(next_move_coord) == 1, f"Cannot move directly from {self.global_location.coord} to {next_move_coord}"

        self.log(f"DEBUG: Moving from {self.global_location.coord} to {next_move_coord}")
        self.move_to(next_move_coord)
        
