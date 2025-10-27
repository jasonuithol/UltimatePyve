import pygame
from dark_libraries.dark_math import Coord
from models.motion import Motion
from models.sprite import Sprite

class Projectile[TSpriteType](tuple):
    __slots__ = ()

    def __new__(
        cls,
        sprite: Sprite[TSpriteType],
        motion: Motion
    ):
        return tuple.__new__(cls, (
            sprite,
            motion,
            pygame.time.get_ticks(), # ticks_at_creation
        ))

    @property
    def sprite(self) -> Sprite[TSpriteType]:
        return self[0]

    @property
    def motion(self) -> Motion:
        return self[1]

    @property
    def ticks_at_creation(self) -> int:
        return self[2]
    
    def get_current_position(self) -> Coord[float]:
        current_ticks = pygame.time.get_ticks()
        time_offset_seconds = (current_ticks - self.ticks_at_creation) / 1000
        return self.motion.get_current_position(time_offset_seconds)
    
    def can_stop(self):
        time_offset_milliseconds = (pygame.time.get_ticks() - self.ticks_at_creation)
        return self.motion.duration < (time_offset_milliseconds / 1000)
    
    def __str__(self) -> str:
        return (
            f"{__class__.__name__}: " 
            + 
            f"sprite={id(self.sprite)}, " 
            + 
            f"motion={self.motion}, " 
            + 
            f"ticks_at_creation={self.ticks_at_creation}"
        )
