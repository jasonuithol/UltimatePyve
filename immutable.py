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

@immutable
class SpriteConfig:
    def __init__(self, tile_size=16, palette="EGA"):
        self.tile_size = tile_size
        self.palette = palette

