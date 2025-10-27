from dark_libraries.dark_math import Coord, Vector2

#
# All spatial units are in the SAME units (generally expected to be unscaled pixels)
#
class Motion(tuple):
    __slots__ = ()

    def __new__(
        cls,
        start_coord: Coord[int],
        end_coord:   Coord[int],
        spatial_units_per_second: float
    ):
        assert start_coord != end_coord, "That's not very dark_engine of you"

        normal_x, normal_y = start_coord.normal(end_coord)

        return tuple.__new__(cls, (
            start_coord,
            end_coord,
            Vector2[float](normal_x, normal_y), # direction_normal
            spatial_units_per_second,
            start_coord.pythagorean_distance(end_coord) / spatial_units_per_second # duration in seconds
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
    def spatial_units_per_second(self) -> float:
        return self[3]
    
    @property
    def duration(self) -> float:
        return self[4]

    def get_current_position(self, time_offset_seconds: float) -> Coord[int]:
        spatial_units_travelled = time_offset_seconds * self.spatial_units_per_second
        return self.start_coord + (self.direction_normal * spatial_units_travelled)

    def __str__(self) -> str:
        return (
            f"{__class__.__name__}: " 
            + 
            f"start_coord={self.start_coord}, " 
            + 
            f"end_coord={self.end_coord}, " 
            + 
            f"direction_normal={self.direction_normal}, "
            + 
            f"spatial_units_per_second={self.spatial_units_per_second}, "
            + 
            f"duration={self.duration}"
        )
