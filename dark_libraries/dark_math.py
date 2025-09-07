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

    # support for being tuplized with tuple(vector2) -> gives (vector2.x, vector2.y)
    def __iter__(self):
        yield self.x
        yield self.y

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

class Rect(Size, Coord):

    def is_in_bounds(self, coord: Coord) -> bool:
        return self.x <= coord.x < self.w and self.y <= coord.y < self.h

if __name__ == "__main__":
     
    a = Coord(1, 2)
    b = Coord(1, 2)
    assert a == b, "__eq__ has a problem"
    assert hash(a) == hash(b), "__hash__ has a problem"
    assert {a: "one"}[b] == "one", "Being a stable dictionary key is a problem" 

    try:
        a.x = 1
    except:
        print("Coord confirmed immutable")
    
    s = Size(0,0)

    try:
        s.w = 1
    except:
        print("Size confirmed immutable")

    print("All tests passed")
