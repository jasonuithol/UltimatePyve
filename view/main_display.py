# file: display/main_display.py

from enum import Enum
from dark_libraries.dark_math import Coord, Size
from data.global_registry import GlobalRegistry
from services.world_clock import CelestialGlyphCodes, WorldClock
from view.view_port import ViewPort

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

class BorderGlyphCodes(Enum):
    SPACE_IBM_FONT_ID = 0
    RIGHT_PROMPT_IBM_FONT_ID = 2

    BLOCK_GLYPH_IBM_FONT_ID = 127
    TOP_LEFT_CNR_GLYPH_IBM_FONT_ID = 123
    TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID = 124
    BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID = 125
    BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID = 126

class MainDisplay(ScalableComponent):

    # Injectable
    display_config: DisplayConfig
    world_clock: WorldClock
    view_port: ViewPort
    global_registry: GlobalRegistry

    def __init__(self):
        pass 

    def _after_inject(self):
        vp_w, vp_h = (self.display_config.VIEW_PORT_SIZE * self.display_config.TILE_SIZE).to_tuple()
        ic_w, ic_h = (self.display_config.CONSOLE_SIZE * self.display_config.FONT_SIZE).to_tuple()

        super().__init__(
            unscaled_size_in_pixels = Size(
                # width of ViewPort, InteractiveConsole, and 3 border lines.
                vp_w + ic_w + (3 * self.display_config.FONT_SIZE.w),

                # Whichever is the tallest out of ViewPort and InteractiveConsole, then add two border lines either end.
                max(vp_h, ic_h) + (2 * self.display_config.FONT_SIZE.w) # yes width, because we rotate the font blocks.
            ),
            scale_factor = self.display_config.SCALE_FACTOR
        )

        self.size_in_glyphs = self._unscaled_size_in_pixels // self.display_config.FONT_SIZE
        self.viewport_width_in_glyphs = self.view_port.unscaled_size().w // self.display_config.FONT_SIZE.w

        # 6 being half the width of the panorama output of 12 chars.
        self.celestial_char_offset = (self.viewport_width_in_glyphs // 2) - 6

        self._color_black      = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[ 0])
        self._color_dark_blue  = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[ 1])
        self._color_light_grey = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[ 7])
        self._color_yellow     = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[14])
        self._color_white      = self._unscaled_surface.map_rgb(self.display_config.EGA_PALETTE[15])

    def init(self):
        
        #
        # BORDER TOP, BOTTOM, LEFT, RIGHT GLYPHS
        #
        self.right_block_glyph = self.global_registry.font_glyphs.get((
            "IBM.CH", 
            BorderGlyphCodes.BLOCK_GLYPH_IBM_FONT_ID.value
        )).replace_color(
            # Set foreground to blue (this is the thick blue border)
            old_mapped_rgb = self._color_white, 
            new_mapped_rbg = self._color_dark_blue
        ).replace_color(
            # Set background to white (this is the thin white border)
            old_mapped_rgb = self._color_black, 
            new_mapped_rbg = self._color_white
        )
        self.top_block_glyph    = self.right_block_glyph.rotate_90()
        self.left_block_glyph   = self.top_block_glyph.rotate_90()
        self.bottom_block_glyph = self.left_block_glyph.rotate_90()

        #
        # BORDER HORIZONTAL, VERTICAL MIDDLE BORDER GLYPHS
        #
        self.horizontal_block = self.left_block_glyph.overlay_with(
            overlay                = self.right_block_glyph, 
            transparent_mapped_rgb = self._color_dark_blue
        )
        self.vertical_block = self.horizontal_block.rotate_90()

        #
        # BORDER CORNER GLYPHS
        #

        # This is used to fix a gap between the block borders and the right hand side rounded corner glyphs.
        # Use "self._color_black" as the transparency color when overlaying the target corner glyphs.
        self.right_cnr_overlay_glyph = self.global_registry.font_glyphs.get((
            "IBM.CH", 
            BorderGlyphCodes.BLOCK_GLYPH_IBM_FONT_ID.value
        )).replace_color(
            # Change block background to blue.  This will become the "brush"
            old_mapped_rgb = self._color_black,
            new_mapped_rbg = self._color_dark_blue
        ).replace_color(
            # Change block foreground to black.  This will become the "transparency"
            old_mapped_rgb = self._color_white,
            new_mapped_rbg = self._color_black
        )

        # Make the glyphs blue foreground and black background.        
        corner_maker_func = lambda font_id: self.global_registry.font_glyphs.get(("IBM.CH", font_id)).replace_color(self._color_white, self._color_dark_blue)

        self.top_left_cnr_glyph     = corner_maker_func(BorderGlyphCodes.TOP_LEFT_CNR_GLYPH_IBM_FONT_ID.value)
        self.bottom_left_cnr_glyph  = corner_maker_func(BorderGlyphCodes.BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID.value)

        # These two will get "fixed" by the overlay we made earlier.
        self.top_right_cnr_glyph    = corner_maker_func(BorderGlyphCodes.TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID.value).overlay_with(self.right_cnr_overlay_glyph, self._color_black)
        self.bottom_right_cnr_glyph = corner_maker_func(BorderGlyphCodes.BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID.value).overlay_with(self.right_cnr_overlay_glyph, self._color_black)

        # Just a big old block of blue.
        self.junction_glyph = self.global_registry.font_glyphs.get(("IBM.CH", BorderGlyphCodes.SPACE_IBM_FONT_ID.value)).replace_color(self._color_black, self._color_dark_blue)

        #
        # CELESTIAL GLYPHS
        #

        # The sun and moon phases.  The sun is yellow and the moons are light grey.
        self.celestial_glyphs = {
            celestial_glyph_code.value:
            self.global_registry.font_glyphs.get(("RUNES.CH", celestial_glyph_code.value)).replace_color(
                self._color_white, 
                self._color_yellow if celestial_glyph_code == CelestialGlyphCodes.SUN else self._color_light_grey
            )
            for celestial_glyph_code in CelestialGlyphCodes
        }

        # A blank space.
        self.celestial_glyphs[0] = self.global_registry.font_glyphs.get(("IBM.CH", BorderGlyphCodes.SPACE_IBM_FONT_ID.value))

        #
        # PROMPTS
        #
        # TODO: Still havent quite got this right
        #

        # Make a blue right-pointing rounded triangle, and then shift it left 1 pixel.
        self.right_prompt_overlay = self.global_registry.font_glyphs.get(("IBM.CH", BorderGlyphCodes.RIGHT_PROMPT_IBM_FONT_ID.value)).replace_color(self._color_white, self._color_dark_blue)
        self.right_prompt_overlay._surface.scroll(dx = -1, dy = 0)

        # Fetch a default white right-pointing rounded triangle, and then overlay the shifted blue triangle over it, using black as the transparency color.
        # The result is supposed to be a blue triangle with a thin white border.  It almost but not quite works.
        self.right_prompt = self.global_registry.font_glyphs.get(("IBM.CH", BorderGlyphCodes.RIGHT_PROMPT_IBM_FONT_ID.value)).overlay_with(
            overlay = self.right_prompt_overlay,
            transparent_mapped_rgb = self._color_black
        )

        # Whatever we achieved above, make a left-pointing version of that.
        self.left_prompt = self.right_prompt.rotate_90().rotate_90()

        # The borders only need to be drawn once.
        self.draw_borders()

    def draw_borders(self):
        surf = self.get_input_surface()

        char_x_middle = self.viewport_width_in_glyphs + 1
        char_x_right  = self.size_in_glyphs.w - 1

        char_y_bottom = self.size_in_glyphs.h - 1

        # Blue borders
        for char_y in range(self.size_in_glyphs.h):
            self.left_block_glyph.blit_to_surface( Coord(            0, char_y), surf)
            self.horizontal_block.blit_to_surface( Coord(char_x_middle, char_y), surf)
            self.right_block_glyph.blit_to_surface(Coord(char_x_right , char_y), surf)
        for char_x in range(self.size_in_glyphs.x):
            self.top_block_glyph.blit_to_surface(   Coord(char_x,             0), surf)
            self.bottom_block_glyph.blit_to_surface(Coord(char_x, char_y_bottom), surf)

        # corners
        self.top_left_cnr_glyph.blit_to_surface(Coord(0, 0), surf)
        self.top_right_cnr_glyph.blit_to_surface(Coord(char_x_right, 0), surf)
        self.bottom_left_cnr_glyph.blit_to_surface(Coord(0, char_y_bottom), surf)
        self.bottom_right_cnr_glyph.blit_to_surface(Coord(char_x_right, char_y_bottom), surf)

        # junctions
        self.junction_glyph.blit_to_surface(Coord(char_x_middle,             0), surf)
        self.junction_glyph.blit_to_surface(Coord(char_x_middle, char_y_bottom), surf)

        # prompts - celestial
        self.right_prompt.blit_to_surface(Coord(self.celestial_char_offset, 0), surf)
        self.left_prompt.blit_to_surface(Coord(self.viewport_width_in_glyphs - self.celestial_char_offset + 1, 0), surf)

        # prompts - wind direction
        self.right_prompt.blit_to_surface(Coord(self.celestial_char_offset + 1, char_y_bottom), surf)
        self.left_prompt.blit_to_surface(Coord(self.viewport_width_in_glyphs - self.celestial_char_offset + 1, char_y_bottom), surf)

    def draw_celestial_panorama(self):

        surf = self.get_input_surface()

        # Sun and moons

        for cursor, glyph_code in enumerate(self.world_clock.get_celestial_panorama()):
            glyph = self.celestial_glyphs[glyph_code]
            glyph.blit_to_surface(Coord(self.celestial_char_offset + cursor + 1, 0), surf)

    def draw_wind_direction(self):
        surf = self.get_input_surface()
        char_y_bottom = self.size_in_glyphs.h - 1

        for cursor, glyph in enumerate(self.global_registry.font_glyphs.get(("IBM.CH", "East  Winds"))):
            glyph.blit_to_surface(Coord(self.celestial_char_offset + cursor + 2, char_y_bottom), surf)

    def draw(self):
        self.draw_celestial_panorama()
        self.draw_wind_direction()

