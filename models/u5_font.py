from dark_libraries.dark_math import Size

class U5Font(tuple):
    __slots__ = ()

    def __new__(
        cls,
        data: list[bytearray],
        char_size: Size,
    ):
        return tuple.__new__(cls, (
            data,
            char_size,
        ))

    @property
    def data(self) -> list[bytearray]:
        return self[0]

    @property
    def char_size(self) -> Size:
        return self[1]