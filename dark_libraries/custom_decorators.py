# file: dark_libraries/custom_decorators.py
def immutable(cls):
    orig_setattr = cls.__setattr__
    def locked_setattr(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(f"{cls.__name__} is immutable — cannot modify '{name}'")
        orig_setattr(self, name, value)
    cls.__setattr__ = locked_setattr

    orig_init = cls.__init__
    def new_init(self, *args, **kwargs):
        self._frozen = False

        # if this line throws a TypeError, move your @immutable decorator above the other decorators esp. @dataclass
        orig_init(self, *args, **kwargs)
        
        self._frozen = True
    cls.__init__ = new_init
    return cls

import inspect
from typing import get_type_hints

def auto_init(cls):
    # Merge annotations from MRO (base first)
    annotations = {}
    for base in reversed(cls.__mro__):
        annotations.update(getattr(base, '__annotations__', {}))

    # Grab type hints (resolves forward refs, includes extras)
    type_hints = get_type_hints(cls, include_extras=True)

    # Build parameter list for the signature
    params = [inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    for name in annotations:
        default = getattr(cls, name, inspect._empty)
        params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=type_hints.get(name, inspect._empty)
            )
        )

    # The actual __init__ implementation
    def __init__(self, *args, **kwargs):
        if len(args) > len(annotations):
            raise TypeError(f"Expected at most {len(annotations)} positional arguments")
        for name, value in zip(annotations.keys(), args):
            setattr(self, name, value)
        for name in list(annotations.keys())[len(args):]:
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
            elif hasattr(cls, name):
                setattr(self, name, getattr(cls, name))
            else:
                raise TypeError(f"Missing value for '{name}'")
        if kwargs:
            raise TypeError(f"Got unexpected keyword arguments: {', '.join(kwargs)}")

    # Attach a proper signature and annotations
    __init__.__signature__ = inspect.Signature(params)
    __init__.__annotations__ = {"return": None, **type_hints}

    cls.__init__ = __init__
    return cls