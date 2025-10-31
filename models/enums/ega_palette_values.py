from enum import Enum

class EgaPaletteValues(Enum):
    Black = (0,   0,   0)
    Blue  = (0,   0, 170)
    Green = (0, 170,   0)
    Cyan  = (0, 170, 170)

    Red       = (170,   0,   0)
    Magenta   = (170,   0, 170)
    Brown     = (170,  85,   0)
    LightGrey = (170, 170, 170)

    DarkGrey   = (85,  85,  85)
    LightBlue  = (85,  85, 255)
    LightGreen = (85, 255,  85)
    LightCyan  = (85, 255, 255)

    LightRed     = (255,  85,  85)
    LightMagenta = (255,  85, 255)
    Yellow       = (255, 255,  85)
    White        = (255, 255, 255)

    @classmethod
    def from_index(cls, index: int):
        if not hasattr(cls, '_as_list'):
            cls._as_list = list(cls)
        return cls._as_list[index]