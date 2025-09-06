# file: the_ugly_corner/custom_decorators.py
import functools, makefun

def immutable(cls):
    orig_setattr = cls.__setattr__
    def locked_setattr(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(f"{cls.__name__} is immutable — cannot modify '{name}'")
        orig_setattr(self, name, value)
    cls.__setattr__ = locked_setattr

    orig_init = cls.__init__
    @functools.wraps(orig_init)
    def new_init(self, *args, **kwargs):
        self._frozen = False
        orig_init(self, *args, **kwargs)
        self._frozen = True
    cls.__init__ = new_init
    return cls

import inspect
from typing import get_type_hints

def auto_init(cls):
    annotations = get_type_hints(cls)
    params = [inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)]

    for name, annotation in annotations.items():
        default = getattr(cls, name, inspect.Parameter.empty)
        param = inspect.Parameter(
            name,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
            annotation=annotation
        )
        params.append(param)

    signature = inspect.Signature(params)

    @makefun.with_signature(signature)
    def __init__(self, *args, **kwargs):
        bound = signature.bind(self, *args, **kwargs)
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            if name != "self":
                setattr(self, name, value)

    cls.__init__ = __init__
    return cls