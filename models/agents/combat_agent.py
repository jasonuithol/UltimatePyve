import random
from typing import Self

from dark_libraries.dark_math import Coord
from models.sprite import Sprite

from .npc_agent import NpcAgent

class CombatAgent(NpcAgent):

    def __init__(self, coord: Coord, sprite: Sprite):
        super().__init__()
        self._coord = coord
        self._sprite = sprite

    # NPC_AGENT IMPLEMENTATION (Partial): Start
    @property
    def current_tile(self):
        return self._sprite.get_current_frame_tile()

    @property
    def coord(self) -> Coord:
        return self._coord
    
    @coord.setter
    def coord(self, value: Coord):
        self._coord = value
    # NPC_AGENT IMPLEMENTATION (Partial): End

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
