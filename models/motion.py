from dark_libraries.dark_math import Coord, Vector2

#
# All spatial units are in the SAME units (generally expected to be unscaled pixels)
#
class Motion(tuple):
    __slots__ = ()

    def __new__(
        cls,
        start_world_coord: Coord[int],
        end_world_coord:   Coord[int],
        spatial_units_per_second: float
    ):
        normal_x, normal_y = start_world_coord.normal(end_world_coord)

        return tuple.__new__(cls, (
            start_world_coord,
            end_world_coord,
            Vector2[float](normal_x, normal_y), # direction_normal
            spatial_units_per_second,
            start_world_coord.pythagorean_distance(end_world_coord) / spatial_units_per_second # duration in seconds
        ))

    @property
    def start_world_coord(self) -> Coord[int]:
        return self[0]

    @property
    def end_world_coord(self) -> Coord[int]:
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

    def get_current_position(self, time_offset_seconds: float) -> Coord[float]:
        spatial_units_travelled = time_offset_seconds * self.spatial_units_per_second
        return self.start_world_coord + (self.direction_normal * spatial_units_travelled)

    def __str__(self) -> str:
        return (
            f"{__class__.__name__}: " 
            + 
            f"start_world_coord={self.start_world_coord}, " 
            + 
            f"end_world_coord={self.end_world_coord}, " 
            + 
            f"direction_normal={self.direction_normal}, "
            + 
            f"spatial_units_per_second={self.spatial_units_per_second}, "
            + 
            f"duration={self.duration}"
        )
