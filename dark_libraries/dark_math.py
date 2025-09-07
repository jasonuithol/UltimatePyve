# file: dark_libraries/dark_math.py

from typing import Self
from dark_libraries.custom_decorators import immutable, auto_init

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

    def to_tuple(self):
        return (self.x, self.y)

    # support for being a Dict key, will also support "v1 == v2" logical expression
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.x == other.x and self.y == other.y

    # support for being a Dict key
    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
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
    
    def __iter__(self):
        for y in range(self.h):
            for x in range(self.w):
                yield x, y

class Rect(Size, Coord):

    def __init__(self, corner: Coord, size: Size):
        self.x = corner.x
        self.y = corner.y
        self.w = size.w
        self.h = size.h

    def is_in_bounds(self, coord: Coord) -> bool:
        return self.x <= coord.x < (self.w + self.x) and self.y <= coord.y < (self.h + self.y)

    def __iter__(self):
        for y in range(self.y, self.h + self.y):
            for x in range(self.x, self.w + self.x):
                yield x, y

if __name__ == "__main__":
     
    a = Coord(1, 2)
    b = Coord(1, 2)
    assert a == b, "__eq__ has a problem"
    assert hash(a) == hash(b), "__hash__ has a problem"
    assert {a: "one"}[b] == "one", "Being a stable dictionary key is a problem" 

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

    assert len(list(s)) == s.w * s.h, "Wrong number of iterated coords in Rect"


    r = Rect(Coord(3,3), Size(4,4))

    assert r.is_in_bounds(Coord(5,5)), "Rect failed is in bounds"
    assert not r.is_in_bounds(Coord(50,50)), "Rect failed not in bounds"

    assert len(list(r)) == r.w * r.h, "Wrong number of iterated coords in Rect"

    print("All tests passed")
