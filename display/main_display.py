# file: display/main_display.py

from dark_libraries.dark_math import Coord, Size
from display.u5_font import U5FontRegistry, U5Glyph
from display.view_port import ViewPort
from game.world_clock import WorldClock

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

BLOCK_GLYPH_IBM_FONT_ID = 127

class MainDisplay(ScalableComponent):

    BORDER_THICCNESS = 8

    # Injectable
    display_config: DisplayConfig
    world_clock: WorldClock
    view_port: ViewPort
    u5_font_registry: U5FontRegistry

    def __init__(self):
        pass 

    def _after_inject(self):
        print(self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE).to_tuple())
        vp_w, vp_h = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE).to_tuple()
        ic_w, ic_h = self.display_config.CONSOLE_SIZE.scale(self.display_config.FONT_SIZE).to_tuple()

        super().__init__(
            unscaled_size_in_pixels = Size(
                vp_w + ic_w + (3 * MainDisplay.BORDER_THICCNESS),
                max(vp_h, ic_h) + (2 * MainDisplay.BORDER_THICCNESS)
            ),
            scale_factor = self.display_config.SCALE_FACTOR
        )

        self.size_in_glyphs = Size(
            self._unscaled_size_in_pixels.w // self.display_config.FONT_SIZE.w, 
            self._unscaled_size_in_pixels.h // self.display_config.FONT_SIZE.h
        )

        self.viewport_width_in_glyphs = self.view_port.unscaled_size().w // self.display_config.FONT_SIZE.w
        self.celestial_char_offset = ((self.viewport_width_in_glyphs - 12) // 2) + 1

        self._bordercolor       = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[ 1]) # dark blue
        self._celestial_color   = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[15]) # dark blue

        # TODO: Get this from the EGA-PALETTE
#        self._back_color = self._unscaled_surface.map_rgb((0,0,255))
#        self._clear()

    def _make_glyph(self, glyph_data: bytearray, fore_color: int):
        return U5Glyph(
            data = glyph_data,
            glyph_size = self.display_config.FONT_SIZE,
            foreground_color_mapped_rgb = fore_color,
            background_color_mapped_rgb = self._back_color
        )

    def init(self):

        self.ibm_font = self.u5_font_registry.get_font("IBM.CH")
        self.rune_font = self.u5_font_registry.get_font("RUNES.CH")
        
        block_glyph_data = self.ibm_font.map_codes([BLOCK_GLYPH_IBM_FONT_ID])[0]
        self.block_glyph = self._make_glyph(block_glyph_data, self._bordercolor)


        '''
        self.top_left_glyph = U5Glyph(
            data = rune_font.,
            glyph_size = self.display_config.,
            foreground_color_mapped_rgb: int,
            background_color_mapped_rgb: int
        )
        '''

        '''
        vp_x, vp_y = 0,0
        ic_x, ix_y = vp_w, vp_h - ic_h
        '''

    def draw(self):
        surf = self.get_input_surface()

        # Blue borders
        for char_y in range(self.size_in_glyphs.h):
            self.block_glyph.blit_to_surface(Coord(0                                , char_y), surf)
            self.block_glyph.blit_to_surface(Coord(self.viewport_width_in_glyphs + 1, char_y), surf)
            self.block_glyph.blit_to_surface(Coord(self.size_in_glyphs.w - 1        , char_y), surf)
        for char_x in range(self.size_in_glyphs.x):
            self.block_glyph.blit_to_surface(Coord(char_x, 0), surf)
            self.block_glyph.blit_to_surface(Coord(char_x, self.size_in_glyphs.h - 1), surf)

        # Sun and moons
        for cursor, glyph_code in enumerate(self.world_clock.get_celestial_panorama()):
            glyph_data = self.rune_font.data[glyph_code]
            glyph = self._make_glyph(glyph_data, self._celestial_color)
            glyph.blit_to_surface(Coord(self.celestial_char_offset + cursor, 0), surf)




    
