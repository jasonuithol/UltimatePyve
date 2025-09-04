
from dataclasses import dataclass
from dark_libraries.dark_math import Size
from display.view_port import ViewPort

@dataclass
class MainDisplay:
    view_port: ViewPort

    def size_in_pixels(self) -> Size:
        return self.view_port.view_size_in_pixels_scaled()