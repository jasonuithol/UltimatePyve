import random

from typing import Iterable, Self
from copy import copy

from dark_libraries.dark_math import Coord, Rect
from dark_libraries.logging import LoggerMixin

from models.global_location import GlobalLocation
from models.sprite import Sprite

class NpcAgent(LoggerMixin):

    def __init__(self, sprite: Sprite, global_location: GlobalLocation):
        super().__init__()

        assert not sprite is None, "sprite must be set"
        assert not global_location is None, "global_location must be set"

        self.sprite = sprite
        self.global_location = global_location

    @property
    def tile_id(self) -> int: ...

    @property
    def name(self) -> str: ...

    @property
    def strength(self) -> int: ...

    @property
    def dexterity(self) -> int: ...

    @property
    def armour(self) -> int: ...

    @property
    def maximum_hitpoints(self) -> int: ...

    @property 
    def hitpoints(self) -> int: ...

    @hitpoints.setter
    def hitpoints(self, val: int): ...

    def get_damage(self, attack_type: chr) -> int: ...


    def get_coord(self) -> Coord:
        return self.global_location.coord
    
    def move_to(self, coord: Coord):
        self.global_location = self.global_location.move_to_coord(coord)

    def calculate_hit_probability(self, target: Self) -> float:
        to_hit   = 0.5 + (0.5 * self.dexterity / 30) 
        to_dodge = 0.1 + (0.5 * (target.dexterity + target.armour) / 60)
        return to_hit * to_dodge    

    # Attack Type = L, R or B for handedness
    def calculate_damage(self, attack_type: chr) -> int:
        damage_penalty = 0.5 + (0.5 * self.strength / 30)
        return self.get_damage(attack_type) * damage_penalty
        
    def take_damage(self, damage: int) -> bool:
        self.hitpoints = self.hitpoints - damage

        self.hitpoints = min(self.hitpoints, 0)
        self.hitpoints = max(self.hitpoints, self.maximum_hitpoints)

    def attack(self, other: Self):
        if random.uniform(0, 1) < self.calculate_hit_probability(other):
            damage = self.calculate_damage()
            other.take_damage(damage)

    def spawn_clone_at(self, coord: Coord) -> Self:
        other = copy(self)
        other.move_to(coord)
        return other
    
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
    