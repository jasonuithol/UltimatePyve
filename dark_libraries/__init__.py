# file: dark_libraries/__init__.py
from .custom_decorators import immutable, auto_init
from .dark_math import Coord, Size, Rect

__all__ = [
    'immutable', 
    'auto_init',
    'Coord', 
    'Size', 
    'Rect'
]