# file: the_ugly_corner/freezable.py

from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class Response(Generic[T]):
    __slots__ = ("value", "error")

    def __init__(self, value: Optional[T] = None, error: Optional[str] = None):
        self.value = value
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self):
        if self.success:
            return f"Response(success, value={self.value!r})"
        else:
            return f"Response(error={self.error!r})"

from copy import copy 
from contextlib import contextmanager
from functools import wraps

class Freezable:
    def __init__(self):
        object.__setattr__(self, "_frozen", False)  # bypasses __setattr__

    def _freeze(self):
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name, value):
        if name != "_frozen" and getattr(self, "_frozen", False):
            raise AssertionError(
                f"Cannot set frozen {self.__class__.__name__!r}.{name!r} with new value {value!r}. "
                f"Use 'with self.mutate() as mutated:' instead."
            )
        super().__setattr__(name, value)

    @contextmanager
    def mutate(self):
        new = copy(self)
        object.__setattr__(new, "_frozen", False)  # ensure clone starts mutable
        try:
            yield new
        finally:
            object.__setattr__(new, "_frozen", True)

def mutator(method):
    @wraps(method)
    def wrapper(self: Freezable, *args, **kwargs):
        assert isinstance(self, Freezable), f"Object of class {type(self).__name__!r} is not a subtype of Freezable."
        with self.mutate() as new:
            result = method(new, *args, **kwargs)
        # If your mutate() already freezes on exit, result/new are frozen here
        return result if result is not None else new
    return wrapper

