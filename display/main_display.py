# file: display/main_display.py

from dark_libraries import Size
from .view_port import ViewPort

class MainDisplay:
    view_port: ViewPort

    def size_in_pixels(self) -> Size:
        return self.view_port.view_size_in_pixels_scaled()