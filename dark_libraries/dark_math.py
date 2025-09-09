# file: dark_libraries/dark_math.py

from typing import Iterable, Self
from .custom_decorators import immutable, auto_init

@immutable
@auto_init
class Vector2:
    x: int
    y: int

    def scale(self, s: int) -> Self:
         return self.__class__(self.x * s, self.y * s)
    
    def add(self, other: Self) -> Self:
            return self.__class__(self.x + other.x, self.y + other.y)

    def subtract(self, other: Self) -> Self:
            return self.__class__(self.x - other.x, self.y - other.y)

    def to_tuple(self) -> tuple[int,int]:
        return (self.x, self.y)

    # support for being a Dict key, will also support "v1 == v2" logical expression
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.x == other.x and self.y == other.y

    # support for being a Dict key
    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x={self.x},y={self.y})"

class Coord(Vector2):
    pass

class Size(Vector2):
    @property
    def w(self) -> int:
        return self.x

    @w.setter
    def w(self, value: int):
        self.x = value

    @property
    def h(self) -> int:
        return self.y

    @h.setter
    def h(self, value: int):
        self.y = value

    def is_in_bounds(self, coord: Coord) -> bool:
        return 0 <= coord.x < self.w and 0 <= coord.y < self.h
    
    def to_rect(self, minimum_corner: Coord) -> 'Rect':
        return Rect(minimum_corner, self)
    
    def to_offset(self) -> Coord:
        return Coord(self.w, self.h)

    def __iter__(self) -> Iterable[Coord]:
        for y in range(self.h):
            for x in range(self.w):
                yield Coord(x, y)

@immutable
class Rect(Size, Coord):

    def __init__(self, minimum_corner: Coord, size: Size):
        self.minimum_corner = minimum_corner
        self.size = size

    def is_in_bounds(self, coord: Coord) -> bool:
        shifted_coord = coord.subtract(self.minimum_corner)
        return self.size.is_in_bounds(shifted_coord)
    
    def move(self, offset: Coord) -> Self:
        return Rect(self.minimum_corner.add(offset), self.size())

    def __iter__(self) -> Iterable[tuple[int,int]]:
        self.minimum_corner
        for offset in self.size:
            yield self.minimum_corner.add(offset)

#
# MAIN: Tests
#
if __name__ == "__main__":
     
    a = Coord(1, 2)
    b = Coord(1, 2)
    assert a == b, "__eq__ has a problem"
    assert hash(a) == hash(b), "__hash__ has a problem"
    assert {a: "one"}[b] == "one", "Being a stable dictionary key is a problem" 

    assert a.subtract(b) == Coord(0,0), "subtract bokrne"

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


    r = Rect(Coord(3,3), Size(4,4))

    assert r.is_in_bounds(Coord(5,5)), "Rect failed is in bounds"
    assert not r.is_in_bounds(Coord(50,50)), "Rect failed not in bounds"

    for coord in r:
        assert r.is_in_bounds(coord), "Rect generated an out of bounds iteratant"

    assert len(list(r)) == r.size.w * r.size.h, "Wrong number of iterated coords in Rect"

    try:
        immutable = False
        r.w = 42
    except:
        print("Rect confirmed immutable")
        immutable = True

    assert immutable == True, "Rect failed immutable test"

    print("All tests passed")
