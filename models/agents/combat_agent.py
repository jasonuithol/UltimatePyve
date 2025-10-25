from copy import copy
import random
from typing import Self

from dark_libraries.dark_math import Coord
from models.sprite import Sprite
from models.tile import Tile

from .npc_agent import NpcAgent

class CombatAgent(NpcAgent):

    def __init__(self, coord: Coord[int], sprite: Sprite[Tile]):
        super().__init__()
        self._coord = coord
        self._sprite = sprite
        self._sprite_time_offset = sprite.create_random_time_offset()

    # NPC_AGENT IMPLEMENTATION (Partial): Start
    @property
    def current_tile(self):
        return self._sprite.get_current_frame(self._sprite_time_offset)

    @property
    def coord(self) -> Coord[int]:
        return self._coord
    
    @coord.setter
    def coord(self, value: Coord[int]):
        self._coord = value
    # NPC_AGENT IMPLEMENTATION (Partial): End

    @property
    def strength(self) -> int: ...

    @property
    def armour(self) -> int: ...

    @property
    def maximum_hitpoints(self) -> int: ...

    @property 
    def hitpoints(self) -> int: ...

    @hitpoints.setter
    def hitpoints(self, val: int): ...

    def get_damage(self, attack_type: chr) -> int: ...

    def calculate_hit_probability(self, target: Self) -> float:
        to_hit   = 0.5 + (0.5 * self.dexterity / 30) 
        to_dodge = 0.1 + (0.5 * (target.dexterity + target.armour) / 60)
        return to_hit * to_dodge    

    # Attack Type = L, R or B for handedness
    def calculate_damage(self, attack_type: str) -> int:
        damage_penalty = 0.5 + (0.5 * self.strength / 30)
        return int(self.get_damage(attack_type) * damage_penalty)
        
    def take_damage(self, damage: int) -> bool:
        self.hitpoints = self.hitpoints - damage

        self.hitpoints = max(self.hitpoints, 0)
        self.hitpoints = min(self.hitpoints, self.maximum_hitpoints)

        self.log(f"{self.name} took damage={damage} to change hitpoints {self.hitpoints} -> {self.hitpoints}")

    def attack(self, other: Self) -> bool:
        if random.uniform(0.0, 1.0) < self.calculate_hit_probability(other):
            #
            # TODO: Get both hands involved.
            #
            damage = self.calculate_damage(attack_type="R")
            other.take_damage(damage)

            # Attack succeeded
            self.log(f"DEBUG: Attack succeeded with to_hit probability={self.calculate_hit_probability(other)}, damage={damage}") 
            return True
        else:
            # Attack failed (missed)
            self.log(f"DEBUG: Attack missed with to_hit probability={self.calculate_hit_probability(other)}") 
            return False

    def spawn_clone_at(self, coord: Coord[int]) -> Self:
        other = copy(self)
        other.coord = coord
        other._sprite_time_offset = self._sprite.create_random_time_offset()
        # DO NOT RESET SPENT ACTION POINTS
        return other

    def enter_combat(self, coord: Coord[int]):
        self.coord = coord
        self._spent_action_points = 0


