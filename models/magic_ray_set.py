from dark_libraries.dark_math import Coord
from models.enums.ega_palette_values import EgaPaletteValues

class MagicRaySet(tuple):
    __slots__ = ()

    def __new__(
        cls,
        origin:     Coord[float],
        color:      EgaPaletteValues,
        end_points: set[Coord[float]],
    ):
        return tuple.__new__(cls, (
            origin,
            color,
            end_points,
        ))

    @property
    def origin(self) -> Coord[float]:
        return self[0]

    @property
    def color(self) -> EgaPaletteValues:
        return self[1]

    @property
    def end_points(self) -> set[Coord[float]]:
        return self[2]