from dark_libraries.dark_math import Coord, Vector2

class Motion(tuple):
    __slots__ = ()

    def __new__(
        cls,
        start_coord: Coord[int],
        end_coord:   Coord[int],
        unscaled_pixels_per_second: float,
    ):
        return tuple.__new__(cls, (
            start_coord,
            end_coord,
            start_coord.normal(end_coord), # direction_normal
            unscaled_pixels_per_second,
        ))

    @property
    def start_coord(self) -> Coord[int]:
        return self[0]

    @property
    def end_coord(self) -> Coord[int]:
        return self[1]

    @property
    def direction_normal(self) -> Vector2[float]:
        return self[2]

    @property
    def unscaled_pixels_per_second(self) -> float:
        return self[3]
    
    def get_position(self, time_offset: float) -> Coord[int]:
        return self.direction_normal * time_offset * self.unscaled_pixels_per_second