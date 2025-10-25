# file: dark_libraries/dark_math.py

import math
from typing import Iterable, Self

FOURWAY_NEIGHBOURS = [
    ( 0,  1), # bottom
    ( 0, -1), # top
    ( 1,  0), # right
    (-1,  0), # left
]

EIGHTWAY_NEIGHBOURS = FOURWAY_NEIGHBOURS + [
    ( 1,  1), # bottom-right
    ( 1, -1), # top-right
    (-1,  1), # bottom-left
    (-1, -1)  # bottom-right
]

def is_numeric(s) -> bool:
    return isinstance(s, int) or isinstance(s, float)

TOtherNumeric = int | float
TOtherNumericTuple = tuple[int,int] | tuple[float,float]

class Vector2[TNumeric](tuple):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, x: TNumeric, y: TNumeric):
        return super().__new__(cls, (x, y))
    
    @property
    def x(self) -> TNumeric: return self[0]

    @property
    def y(self) -> TNumeric: return self[1]

    def scale(self, s: TOtherNumeric | TOtherNumericTuple) -> Self:
        if is_numeric(s):
            return self.__class__(self.x * s, self.y * s)
        elif isinstance(s, tuple) and len(s) >= 2:
            # hope for the best for now.....
            return self.__class__(self.x * s[0], self.y * s[1])
        else:
            raise ValueError(f"Cannot perform Vector2.scale on {s!r}")

    __mul__ = __rmul__ = scale

    def __neg__(self):
        return (0,0) - self

    def floor_div(self, s: TOtherNumeric | TOtherNumericTuple):
        if is_numeric(s):
            return self.__class__(self.x // s, self.y // s)
        elif isinstance(s, tuple) and len(s) >= 2:
            # hope for the best for now.....
            return self.__class__(self.x // s[0], self.y // s[1])
        else:
            raise NotImplemented(f"Cannot perform Vector2.floor_div on {s!r}")

    __floordiv__ = floor_div

    def add(self, other: TOtherNumericTuple) -> Self:
        return self.__class__(self.x + other[0], self.y + other[1])
    
    __add__ = __radd__ = add

    def subtract(self, other: TOtherNumericTuple) -> Self:
        return self.__class__(self.x - other[0], self.y - other[1])

    __sub__ = subtract

    def __rsub__(self, other):
        return self.__class__(other[0] - self.x, other[1] - self.y)

    def pythagorean_distance(self, other: tuple) -> float:
        assert len(other) >= 2, "Argument must have at least two elements."
        return ( ((self[0] - other[0]) ** 2) + ((self[1] - other[1]) ** 2) ) ** 0.5

    def normal(self, other: TOtherNumericTuple) -> tuple[float,float]:
        assert len(other) >= 2, "Argument must have at least two elements."
        distance = self.pythagorean_distance(other)
        assert not (distance == 0), "Cannot call normal when self == other"
        return ((other[0] - self[0]) / distance, (other[1] - self[1]) / distance)

    # TODO: must be a faster way of doing this.
    def normal_4way(self, other: tuple[int, int]) -> Self:
        assert len(other) >= 2, "Argument must have at least two elements."
        dx, dy = other[0] - self[0], other[1] - self[1]
        assert not(dx == 0 and dy == 0), f"Cannot call normal_4way when self {self} == other {other}"
        if dx == 0:
            if dy > 0:
                return self.__class__(0, +1)
            else:
                return self.__class__(0, -1)     
        gradient = dy/dx
        if -1 <= gradient < 1: # left or right
            if dx > 0:
                return self.__class__(+1, 0)
            else:
                return self.__class__(-1, 0)
        else:
            if dy > 0:
                return self.__class__(0, +1)
            else:
                return self.__class__(0, -1)

    def taxi_distance(self, other: tuple[int, int]) -> int:
        assert len(other) >= 2, "Argument must have at least two elements."
        return abs(self[0] - other[0]) + abs(self[1] - other[1])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{type(self.x).__name__}](x={self.x},y={self.y})"

    def to_tuple(self) -> tuple[TNumeric, TNumeric]:
        return (self[0], self[1])
    
    def get_4way_neighbours(self) -> list[Self]:
        return [self.add(neighbour) for neighbour in FOURWAY_NEIGHBOURS]

    def get_8way_neighbours(self) -> list[Self]:
        return [self.add(neighbour) for neighbour in EIGHTWAY_NEIGHBOURS]

    def translate_polar(self, pythagorean_distance: float, radians: float) -> Self:
        dx = int(pythagorean_distance * math.cos(radians))
        dy = int(pythagorean_distance * math.sin(radians))
        return self.__class__(self[0] + dx, self[1] + dy)


class Coord[TNumeric](Vector2[TNumeric]):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def to_offset(self) -> Vector2[TNumeric]:
        return Vector2[TNumeric](self.x, self.y)

class Size[TNumeric](Vector2[TNumeric]):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, w: TNumeric, h: TNumeric):
        return tuple.__new__(cls, (w, h))

    @property
    def w(self) -> TNumeric:
        return self[0]

    @property
    def h(self) -> TNumeric:
        return self[1]

    def is_in_bounds(self, coord: Coord[TNumeric]) -> bool:
        return 0 <= coord.x < self.w and 0 <= coord.y < self.h
    
    def to_rect(self, minimum_corner: Coord[TNumeric]) -> 'Rect[TNumeric]':
        return Rect[TNumeric](minimum_corner, self)
    
    def to_offset(self) -> Vector2[TNumeric]:
        return Vector2(self.w, self.h)

    def __iter__(self) -> Iterable[Coord[TNumeric]]:
        for y in range(self.h):
            for x in range(self.w):
                yield Coord(x, y)

class Rect[TNumeric](tuple):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, minimum_corner: tuple[TNumeric ,TNumeric], size: tuple[TNumeric, TNumeric]):
        return super().__new__(cls, (minimum_corner[0], minimum_corner[1], size[0], size[1]))

    @property
    def x(self) -> TNumeric: return self[0]

    @property
    def y(self) -> TNumeric: return self[1]

    @property
    def w(self) -> TNumeric: return self[2]

    @property
    def h(self) -> TNumeric: return self[3]

    @property
    def size(self) -> Size[TNumeric]: return Size[TNumeric](self.w, self.h)

    @property
    def minimum_corner(self) -> Coord[TNumeric]: return Coord[TNumeric](self.x, self.y)

    def is_in_bounds(self, coord: tuple[TNumeric,TNumeric]) -> bool:
        return self.x <= coord[0] < self.w + self.x and self.y <= coord[1] < self.h + self.y

    def __iter__(self) -> Iterable[Coord[TNumeric]]:
        for y in range(self.y, self.y + self.h):
            for x in range(self.x, self.x + self.w):
                yield Coord[TNumeric](x, y)

    def to_tuple(self) -> tuple[TNumeric, TNumeric]:
        return self.x, self.y, self.w, self.h

#
# MAIN: Tests
#
if __name__ == "__main__":

    a = Coord(1, 2)
    b = Coord(1, 2)
    assert a == b, "__eq__ has a problem"
    assert hash(a) == hash(b), "__hash__ has a problem"
    assert {a: "one"}[b] == "one", "Being a stable dictionary key is a problem" 

    assert a.subtract(b) == Coord(0,0), f"subtract bokrne: expected 0,0 got {a.subtract(b)}"

    x = Vector2(10, 10)

    assert x + (10,10) == Vector2(20,20), "__add__ is broken"
    assert isinstance((x + (3,3)).x, int), "__add__(int) doesn't return Vector2[int,int]"
    assert (10,10) + x == Vector2(20,20), "__radd__ is broken"
    
    assert x - (10,10) == Vector2(0,0), "__sub__ is broken"
    assert (5, 5) - x == Vector2(-5, -5), f"__rsub broken, expected Vector2(-5,-5), got {(5, 5) - x!r}"

    assert x // 2 == Vector2(5,5), "Floor div broken"
    assert x * 3 == Vector2(30,30), "__mul__(int) broke"
    assert isinstance((x * 3).x, int), "__mul__(int) doesn't return Vector2[int,int]"
    assert 3 * x == Vector2(30,30), "__rmul__(int) broke"
    assert x * (3,4) == Vector2(30,40), "__mul__(int) broke"
    assert (3,4) * x == Vector2(30,40), "__rmul__(int) broke"

    assert -x == Vector2(-10,-10), "__neg__ broke"

    assert Vector2(10,10).pythagorean_distance((13,14)) == 5, "Pythagorean distance broken"
    assert Vector2(10,10).taxi_distance((13,14)) == 7, "Taxi distance broken"

    try:
        immutable = False
        a.x = 1
    except:
        immutable = True
        print("Coord confirmed immutable")
    
    assert immutable == True, "Coord failed immutable test"

    s = Size(5,10)
    try:
        immutable = False
        s.w = 1
    except:
        print("Size confirmed immutable")
        immutable = True

    assert immutable == True, "Size failed immutable test"

    for coord in s:
        assert s.is_in_bounds(coord), "Size generated an out of bounds iteratant"

    assert len(list(s)) == s.w * s.h, "Wrong number of iterated coords in Rect"


    r = Rect[int](Coord[int](3,3), Size(4,4))

    assert r.is_in_bounds(Coord[int](5,5)), "Rect failed is in bounds"
    assert not r.is_in_bounds(Coord[int](50,50)), "Rect failed not in bounds"

    for coord in r:
        assert r.is_in_bounds(coord), "Rect generated an out of bounds iteratant"

    assert len(list(r)) == r.w * r.h, "Wrong number of iterated coords in Rect"

    try:
        immutable = False
        r.w = 42
    except:
        print("Rect confirmed immutable")
        immutable = True

    assert immutable == True, "Rect failed immutable test"

    print("All tests passed")
