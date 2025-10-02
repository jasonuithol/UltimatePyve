# file: dark_libraries/dark_math.py

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

class Vector2(tuple):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, x: int, y: int):
        return super().__new__(cls, (x, y))
    
    @property
    def x(self) -> int: return self[0]

    @property
    def y(self) -> int: return self[1]

    def scale(self, s: int | tuple[int,int]) -> Self:
        if isinstance(s, int):
            return self.__class__(self.x * s, self.y * s)
        elif isinstance(s, tuple) and len(s) >= 2:
            # hope for the best for now.....
            return self.__class__(self.x * s[0], self.y * s[1])
        else:
            raise NotImplemented(f"Cannot perform Vector2.scale on {s!r}")

    __mul__ = __rmul__ = scale

    def __neg__(self):
        return (0,0) - self

    def floor_div(self, s: int | tuple[int, int]):
        if isinstance(s, int):
            return self.__class__(self.x // s, self.y // s)
        elif isinstance(s, tuple) and len(s) >= 2:
            # hope for the best for now.....
            return self.__class__(self.x // s[0], self.y // s[1])
        else:
            raise NotImplemented(f"Cannot perform Vector2.floor_div on {s!r}")

    __floordiv__ = floor_div

    def add(self, other: tuple[int,int]) -> Self:
        return self.__class__(self.x + other[0], self.y + other[1])
    
    __add__ = __radd__ = add

    def subtract(self, other: tuple[int,int]) -> Self:
        return self.__class__(self.x - other[0], self.y - other[1])

    __sub__ = subtract

    def __rsub__(self, other):
        return self.__class__(other[0] - self.x, other[1] - self.y)

    def pythagorean_distance(self, other: tuple) -> float:
        assert len(other) >= 2, "Argument must have at least two elements."
        return ( ((self[0] - other[0]) ** 2) + ((self[1] - other[1]) ** 2) ) ** 0.5

    def taxi_distance(self, other: tuple) -> int:
        assert len(other) >= 2, "Argument must have at least two elements."
        return abs(self[0] - other[0]) + abs(self[1] - other[1])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x={self.x},y={self.y})"

    def to_tuple(self) -> tuple[int, int]:
        return (self[0], self[1])
    
    def get_4way_neighbours(self):
        return [self.add(neighbour) for neighbour in FOURWAY_NEIGHBOURS]

    def get_8way_neighbours(self):
        return [self.add(neighbour) for neighbour in EIGHTWAY_NEIGHBOURS]

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

    def is_in_bounds(self, coord: tuple[int,int]) -> bool:
        return self.x <= coord[0] < self.w + self.x and self.y <= coord[1] < self.h + self.y

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
