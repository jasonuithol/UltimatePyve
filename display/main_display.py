# file: display/main_display.py

from dark_libraries import Size, Vector2
from .interactive_console import InteractiveConsole
from .view_port import ViewPort

class MainDisplay:

    view_port: ViewPort
    interactive_console: InteractiveConsole

    def size_in_pixels(self) -> Size:
        
        vp_w, vp_h = self.view_port.view_size_in_pixels_scaled().to_tuple()
        ic_w, ic_h = self.interactive_console.view_size_in_pixels_scaled().to_tuple()

        vp_x, vp_y = 0,0
        ic_x, ix_y = vp_w, vp_h - ic_h

        return Size(
            vp_w + ic_w,
            max(vp_h, ic_h)
        )
