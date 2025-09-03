# file: immutable.py
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

def auto_init(cls):
    annotations = {}
    # Walk MRO in reverse so base class fields come first
    for base in reversed(cls.__mro__):
        annotations.update(getattr(base, '__annotations__', {}))
    params = list(annotations.keys())

    def __init__(self, *args, **kwargs):
        if len(args) > len(params):
            raise TypeError(f"Expected at most {len(params)} positional arguments")
        # Assign positionals
        for name, value in zip(params, args):
            setattr(self, name, value)
        # Assign remaining from kwargs
        for name in params[len(args):]:
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
            else:
                raise TypeError(f"Missing value for '{name}'")
        if kwargs:
            unexpected = ', '.join(kwargs)
            raise TypeError(f"Got unexpected keyword arguments: {unexpected}")

    cls.__init__ = __init__
    return cls
