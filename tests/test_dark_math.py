import pytest

from dark_libraries.dark_math import Coord, Rect, Size, Vector2


def test_coord_equality_and_hashing():
    a = Coord[int](1, 2)
    b = Coord[int](1, 2)
    assert a == b
    assert hash(a) == hash(b)


def test_coord_is_stable_dict_key():
    a = Coord[int](1, 2)
    b = Coord[int](1, 2)
    assert {a: "one"}[b] == "one"


def test_coord_subtract():
    a = Coord[int](1, 2)
    b = Coord[int](1, 2)
    assert a.subtract(b) == Coord[int](0, 0)


def test_vector2_add():
    x = Vector2[int](10, 10)
    assert x + (10, 10) == Vector2[int](20, 20)
    assert isinstance((x + (3, 3)).x, int)
    assert (10, 10) + x == Vector2[int](20, 20)


def test_vector2_sub():
    x = Vector2[int](10, 10)
    assert x - (10, 10) == Vector2[int](0, 0)
    assert (5, 5) - x == Vector2[int](-5, -5)


def test_vector2_mul_and_floor_div():
    x = Vector2[int](10, 10)
    assert x // 2 == Vector2[int](5, 5)
    assert x * 3 == Vector2[int](30, 30)
    assert isinstance((x * 3).x, int)
    assert 3 * x == Vector2[int](30, 30)
    assert x * (3, 4) == Vector2[int](30, 40)
    assert (3, 4) * x == Vector2[int](30, 40)


def test_vector2_neg():
    x = Vector2[int](10, 10)
    assert -x == Vector2[int](-10, -10)


def test_vector2_distances():
    assert Vector2[int](10, 10).pythagorean_distance((13, 14)) == 5
    assert Vector2[int](10, 10).taxi_distance((13, 14)) == 7


def test_coord_is_immutable():
    a = Coord[int](1, 2)
    with pytest.raises(AttributeError):
        a.x = 1


def test_size_is_immutable():
    s = Size(5, 10)
    with pytest.raises(AttributeError):
        s.w = 1


def test_size_iteration_yields_in_bounds_coords():
    s = Size(5, 10)
    coords = list(s)
    assert all(s.is_in_bounds(c) for c in coords)
    assert len(coords) == s.w * s.h


def test_rect_in_bounds():
    r = Rect[int](Coord[int](3, 3), Size(4, 4))
    assert r.is_in_bounds(Coord[int](5, 5))
    assert not r.is_in_bounds(Coord[int](50, 50))


def test_rect_iteration_yields_in_bounds_coords():
    r = Rect[int](Coord[int](3, 3), Size(4, 4))
    coords = list(r)
    assert all(r.is_in_bounds(c) for c in coords)
    assert len(coords) == r.w * r.h


def test_rect_is_immutable():
    r = Rect[int](Coord[int](3, 3), Size(4, 4))
    with pytest.raises(AttributeError):
        r.w = 42
