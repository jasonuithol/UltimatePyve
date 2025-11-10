import threading
import datetime

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
            datetime.datetime.now() # creation_timestamp
        ))

    @property
    def sprite(self) -> Sprite[TSpriteType]:
        return self[0]

    @property
    def motion(self) -> Motion:
        return self[1]

    @property
    def creation_timestamp(self) -> datetime.datetime:
        return self[2]
    
    def get_current_position(self) -> Coord[float]:
        current_timestamps = datetime.datetime.now()
        time_delta = current_timestamps - self.creation_timestamp
        return self.motion.get_current_position(time_delta.total_seconds())
    
    def can_stop(self):
        current_timestamps = datetime.datetime.now()
        time_delta = current_timestamps - self.creation_timestamp
        return self.motion.duration < time_delta.total_seconds()
    
    def __str__(self) -> str:
        return (
            f"{__class__.__name__}: " 
            + 
            f"sprite={id(self.sprite)}, " 
            + 
            f"motion={self.motion}, " 
            + 
            f"creation_timestamp={self.creation_timestamp}"
        )
