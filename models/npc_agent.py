import random

from typing import Self
from dark_libraries.dark_math import Coord
from copy import copy

from models.global_location import GlobalLocation
from models.npc_metadata import NpcMetadata
from models.sprite import Sprite

class NpcAgent:

    def __init__(self, sprite: Sprite, npc_metadata: NpcMetadata, global_location: GlobalLocation):
        super().__init__()
        self.sprite = sprite
        self.npc_metadata = npc_metadata
        self.global_location = global_location

        self.hitpoints = self.npc_metadata.hitpoints

    @property
    def tile_id(self):
        return self.npc_metadata.npc_tile_id

    @property
    def name(self):
        return self.npc_metadata.name

    def get_coord(self):
        return self.global_location.coord
    
    def move_to(self, coord: Coord):
        self.global_location = self.global_location.move_to_coord(coord)

    def take_damage(self, damage: int) -> bool:
        self.hitpoints = self.hitpoints - damage

        self.hitpoints = min(self.hitpoints, 0)
        self.hitpoints = max(self.hitpoints, self.npc_metadata.hitpoints)

    def attack(self, other: Self):
        if random.uniform(0, 1) < self.npc_metadata.calculate_hit_probability(other.npc_metadata):
            damage = self.npc_metadata.calculate_damage()
            other.take_damage(damage)

    def spawn_clone_at(self, coord: Coord):
        other = copy(self)
        other.move_to(coord)
        return other
    