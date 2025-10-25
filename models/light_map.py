from typing import Self

from dark_libraries.dark_math import Coord, Vector2

class LightMap:

    def __init__(self):
        self.coords_or_offsets: dict[Coord[int] | Vector2[int], int] = {}

    def __str__(self):
        return f"LightMap=" + list(self.coords_or_offsets.keys()).__str__()
    
    def __repr__(self):
        return f"LightMap=" + list(self.coords_or_offsets.keys()).__str__()

    def __iter__(self):
        return self.coords_or_offsets.__iter__()

    def __len__(self):
        return self.coords_or_offsets.__len__()

    def copy(self) -> Self:
        clone = self.__class__()
        clone.coords_or_offsets = self.coords_or_offsets.copy()
        return clone

    def is_lit(self, coord: Coord[int]) -> bool:
        return coord in self.coords_or_offsets.keys()

    def light(self, coord: Coord[int]):
        # will silently ignore duplicate coords, which is perfect.
        self.coords_or_offsets[coord] = 1

    def translate(self, centre_coord: Coord[int]) -> Self:
        translated = LightMap()
        for offset in self.coords_or_offsets.keys():
            translated_coord: Coord[int] = centre_coord + offset
            translated.coords_or_offsets[translated_coord] = 1
        return translated

    def intersect(self, other_coords_or_offsets: set[Coord[int] | Vector2[int]]) -> Self:
        intersected = LightMap()
        for coord_or_offset in self.coords_or_offsets.keys():
            if coord_or_offset in other_coords_or_offsets:
                intersected.coords_or_offsets[coord_or_offset] = 1
        return intersected