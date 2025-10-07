from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Size


@immutable
@auto_init
class U5Font:
    data: list[bytearray]
    char_size: Size
