# file: display/main_display.py

from enum import Enum
from dark_libraries.dark_math import Coord, Size
from display.u5_font import U5FontRegistry, U5Glyph
from display.view_port import ViewPort
from game.world_clock import CelestialGlyphCodes, WorldClock

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

class BorderGlyphCodes(Enum):
    BLOCK_GLYPH_IBM_FONT_ID = 127
    TOP_LEFT_CNR_GLYPH_IBM_FONT_ID = 123
    TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID = 124
    BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID = 125
    BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID = 126

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

        self._bordercolor_fore      = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[ 1]) # dark blue
        self._bordercolor_back      = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[15]) # white
        self._celestial_color_fore  = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[15]) # white
        self._celestial_color_back  = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[ 0]) # black

        # TODO: Get this from the EGA-PALETTE
#        self._back_color = self._unscaled_surface.map_rgb((0,0,255))
#        self._clear()

    def init(self):

        self.ibm_font = self.u5_font_registry.get_font("IBM.CH")
        self.rune_font = self.u5_font_registry.get_font("RUNES.CH")
        
        block_glyph_data = self.ibm_font.data[BorderGlyphCodes.BLOCK_GLYPH_IBM_FONT_ID.value]
        self.right_block_glyph = U5Glyph(
            data = block_glyph_data,
            glyph_size = self.display_config.FONT_SIZE,
            foreground_color_mapped_rgb = self._bordercolor_fore,
            background_color_mapped_rgb = self._bordercolor_back
        )
        self.top_block_glyph    = self.right_block_glyph.rotate_90()
        self.left_block_glyph   = self.top_block_glyph.rotate_90()
        self.bottom_block_glyph = self.left_block_glyph.rotate_90()

        self.top_left_cnr_glyph = U5Glyph(
            data = self.ibm_font.data[BorderGlyphCodes.TOP_LEFT_CNR_GLYPH_IBM_FONT_ID.value],
            glyph_size = self.display_config.FONT_SIZE,
            foreground_color_mapped_rgb = self._bordercolor_fore,
            background_color_mapped_rgb = self._celestial_color_back # black
        )

        self.top_right_cnr_glyph = U5Glyph(
            data = self.ibm_font.data[BorderGlyphCodes.TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID.value],
            glyph_size = self.display_config.FONT_SIZE,
            foreground_color_mapped_rgb = self._bordercolor_fore,
            background_color_mapped_rgb = self._celestial_color_back # black
        )

        self.bottom_left_cnr_glyph = U5Glyph(
            data = self.ibm_font.data[BorderGlyphCodes.BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID.value],
            glyph_size = self.display_config.FONT_SIZE,
            foreground_color_mapped_rgb = self._bordercolor_fore,
            background_color_mapped_rgb = self._celestial_color_back # black
        )

        self.bottom_right_cnr_glyph = U5Glyph(
            data = self.ibm_font.data[BorderGlyphCodes.BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID.value],
            glyph_size = self.display_config.FONT_SIZE,
            foreground_color_mapped_rgb = self._bordercolor_fore,
            background_color_mapped_rgb = self._celestial_color_back # black
        )

        self.celestial_glyphs = {
            celestial_glyph_code.value:
            U5Glyph(
                data = self.rune_font.data[celestial_glyph_code.value],
                glyph_size = self.display_config.FONT_SIZE,
                foreground_color_mapped_rgb = self._celestial_color_fore,
                background_color_mapped_rgb = self._celestial_color_back
            )
            for celestial_glyph_code in CelestialGlyphCodes
        }

        self.celestial_glyphs[0] = U5Glyph(
            data = self.rune_font.data[0],
            glyph_size = self.display_config.FONT_SIZE,
            foreground_color_mapped_rgb = self._celestial_color_fore,
            background_color_mapped_rgb = self._celestial_color_back
        )

    def draw(self):
        surf = self.get_input_surface()

        char_x_middle = self.viewport_width_in_glyphs + 1
        char_x_right  = self.size_in_glyphs.w - 1

        char_y_bottom = self.size_in_glyphs.h - 1

        # Blue borders
        for char_y in range(self.size_in_glyphs.h):
            self.left_block_glyph.blit_to_surface( Coord(            0, char_y), surf)
            self.right_block_glyph.blit_to_surface(Coord(char_x_middle, char_y), surf)
            self.right_block_glyph.blit_to_surface(Coord(char_x_right , char_y), surf)
        for char_x in range(self.size_in_glyphs.x):
            self.top_block_glyph.blit_to_surface(   Coord(char_x,             0), surf)
            self.bottom_block_glyph.blit_to_surface(Coord(char_x, char_y_bottom), surf)

        self.top_left_cnr_glyph.blit_to_surface(Coord(0, 0), surf)
        self.top_right_cnr_glyph.blit_to_surface(Coord(char_x_right, 0), surf)
        self.bottom_left_cnr_glyph.blit_to_surface(Coord(0, char_y_bottom), surf)
        self.bottom_right_cnr_glyph.blit_to_surface(Coord(char_x_right, char_y_bottom), surf)

        # Sun and moons
        for cursor, glyph_code in enumerate(self.world_clock.get_celestial_panorama()):
            glyph = self.celestial_glyphs[glyph_code]
            glyph.blit_to_surface(Coord(self.celestial_char_offset + cursor, 0), surf)




    
