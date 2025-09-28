# file: display/main_display.py

from dark_libraries.dark_math import Size

from .display_config import DisplayConfig

class MainDisplay:

    # Injectable
    display_config: DisplayConfig

    def size_in_pixels(self) -> Size:
        
        vp_w, vp_h = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE).scale(self.display_config.SCALE_FACTOR).to_tuple()
        ic_w, ic_h = self.display_config.CONSOLE_SIZE.scale(self.display_config.FONT_SIZE).scale(self.display_config.SCALE_FACTOR).to_tuple()

        vp_x, vp_y = 0,0
        ic_x, ix_y = vp_w, vp_h - ic_h

        return Size(
            vp_w + ic_w,
            max(vp_h, ic_h)
        )
    
    
