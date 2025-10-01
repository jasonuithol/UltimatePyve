# file: dark_libraries/dark_math.py

from typing import Iterable, Self

class Vector2(tuple):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, x: int, y: int):
        return super().__new__(cls, (x, y))
    
    @property
    def x(self) -> int: return self[0]

    @property
    def y(self) -> int: return self[1]

    def scale(self, s: int | Self) -> Self:
        if isinstance(s, int):
            return self.__class__(self.x * s, self.y * s)
        else:
            # hope for the best for now.....
            return self.__class__(self.x * s.x, self.y * s.y)

    def add(self, other: Self) -> Self:
        return self.__class__(self.x + other.x, self.y + other.y)

    def subtract(self, other: Self) -> Self:
        return self.__class__(self.x - other.x, self.y - other.y)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x={self.x},y={self.y})"

    def to_tuple(self) -> tuple[int, int]:
        return (self[0], self[1])

class Coord(Vector2):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

class Size(Vector2):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, w: int, h: int):
        # WARNING: Bypasses Vector2.__new__
        return tuple.__new__(cls, (w, h))

    @property
    def w(self) -> int:
        return self[0]

    @property
    def h(self) -> int:
        return self[1]

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

class Rect(tuple):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, minimum_corner: tuple[int,int], size: tuple[int,int]):
        return super().__new__(cls, (minimum_corner[0], minimum_corner[1], size[0], size[1]))

    @property
    def x(self) -> int: return self[0]

    @property
    def y(self) -> int: return self[1]

    @property
    def w(self) -> int: return self[2]

    @property
    def h(self) -> int: return self[3]

    @property
    def size(self) -> Size: return Size(self.w, self.h)

    @property
    def minimum_corner(self) -> Coord: return Coord(self.x, self.y)

    def is_in_bounds(self, coord: Coord) -> bool:
        return self.x <= coord.x < self.w + self.x and self.y <= coord.y < self.h + self.y

    def __iter__(self) -> Iterable[Coord]:
        for y in range(self.y, self.y + self.h):
            for x in range(self.x, self.x + self.w):
                yield Coord(x, y)

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

    assert len(list(r)) == r.w * r.h, "Wrong number of iterated coords in Rect"

    try:
        immutable = False
        r.w = 42
    except:
        print("Rect confirmed immutable")
        immutable = True

    assert immutable == True, "Rect failed immutable test"

    print("All tests passed")
