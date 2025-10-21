from enum import Enum
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.enums.ega_palette_values import EgaPaletteValues

from services.font_mapper import FontMapper
from services.surface_factory import SurfaceFactory

from models.border_glyphs import BorderGlyphs

class BlueBorderGlyphCodes(Enum):
    SPACE_IBM_FONT_ID = 0
    RIGHT_PROMPT_IBM_FONT_ID = 2

    BLOCK_GLYPH_IBM_FONT_ID = 127
    LINE_GLYPH_IBM_FONT_ID = 95

    TOP_LEFT_CNR_GLYPH_IBM_FONT_ID = 123
    TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID = 124
    BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID = 125
    BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID = 126

class BlueBorderGlyphFactory(LoggerMixin):

    global_registry: GlobalRegistry
    surface_factory: SurfaceFactory
    font_mapper:     FontMapper

    def load(self):
        self.global_registry.blue_border_glyphs = self._create_border_glyphs()
        self.log("Built blue border glyphs.")

    def _create_border_glyphs(self) -> BorderGlyphs:

        # Be careful changing these colors.
        self._color_black      = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.Black)
        self._color_white      = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.White)

        # Go nuts changing this color.
        self._color_dark_blue  = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.Blue)

        border_glyphs = BorderGlyphs()

        #
        # BORDER TOP, BOTTOM, LEFT, RIGHT GLYPHS
        #
        border_glyphs.right_block_glyph = self.font_mapper.map_code(
            "IBM.CH", 
            BlueBorderGlyphCodes.BLOCK_GLYPH_IBM_FONT_ID.value
        ).replace_color(
            # Set foreground to blue (this is the thick blue border)
            old_mapped_rgb = self._color_white, 
            new_mapped_rbg = self._color_dark_blue
        ).overlay_with(
            overlay = self.font_mapper.map_code(
                "IBM.CH",
                BlueBorderGlyphCodes.LINE_GLYPH_IBM_FONT_ID.value
            ).rotate_90().flip(flip_x = True),
            transparent_mapped_rgb = self._color_black
        )

        border_glyphs.top_block_glyph    = border_glyphs.right_block_glyph.rotate_90()
        border_glyphs.left_block_glyph   = border_glyphs.top_block_glyph.rotate_90()
        border_glyphs.bottom_block_glyph = border_glyphs.left_block_glyph.rotate_90()

        #
        # BORDER HORIZONTAL, VERTICAL MIDDLE BORDER GLYPHS
        #
        border_glyphs.vertical_block = border_glyphs.left_block_glyph.overlay_with(
            overlay                = border_glyphs.right_block_glyph, 
            transparent_mapped_rgb = self._color_dark_blue
        )
        border_glyphs.horizontal_block = border_glyphs.vertical_block.rotate_90()

        #
        # BORDER CORNER GLYPHS
        #

        # This is used to fix a gap between the block borders and the right hand side rounded corner glyphs.
        # Use "self._color_black" as the transparency color when overlaying the target corner glyphs.
        right_cnr_overlay_glyph = self.font_mapper.map_code(
            "IBM.CH", 
            BlueBorderGlyphCodes.BLOCK_GLYPH_IBM_FONT_ID.value
        ).replace_color(
            # Change block background to blue.  This will become the "brush"
            old_mapped_rgb = self._color_black,
            new_mapped_rbg = self._color_dark_blue
        ).replace_color(
            # Change block foreground to black.  This will become the "transparency"
            old_mapped_rgb = self._color_white,
            new_mapped_rbg = self._color_black
        )

        # Make the glyphs blue foreground and black background.        
        corner_maker_func = lambda font_id: self.font_mapper.map_code("IBM.CH", font_id).replace_color(self._color_white, self._color_dark_blue)

        border_glyphs.top_left_cnr_glyph     = corner_maker_func(BlueBorderGlyphCodes.TOP_LEFT_CNR_GLYPH_IBM_FONT_ID.value)
        border_glyphs.bottom_left_cnr_glyph  = corner_maker_func(BlueBorderGlyphCodes.BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID.value)

        # These two will get "fixed" by the overlay we made earlier.
        border_glyphs.top_right_cnr_glyph    = corner_maker_func(BlueBorderGlyphCodes.TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID.value).overlay_with(right_cnr_overlay_glyph, self._color_black)
        border_glyphs.bottom_right_cnr_glyph = corner_maker_func(BlueBorderGlyphCodes.BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID.value).overlay_with(right_cnr_overlay_glyph, self._color_black)

        # Just a big old block of blue.
        border_glyphs.junction_glyph = self.font_mapper.map_code("IBM.CH", BlueBorderGlyphCodes.SPACE_IBM_FONT_ID.value).replace_color(self._color_black, self._color_dark_blue)

        
        #
        # PROMPTS
        #
        # TODO: Still havent quite got this right
        #

        # Make a blue right-pointing rounded triangle, and then shift it left 1 pixel.
        right_prompt_overlay = self.font_mapper.map_code("IBM.CH", BlueBorderGlyphCodes.RIGHT_PROMPT_IBM_FONT_ID.value).replace_color(self._color_white, self._color_dark_blue)
        right_prompt_overlay._surface.scroll(dx = -1, dy = 0)

        # Fetch a default white right-pointing rounded triangle, and then overlay the shifted blue triangle over it, using black as the transparency color.
        # The result is supposed to be a blue triangle with a thin white border.  It almost but not quite works.
        border_glyphs.right_prompt_glyph = self.font_mapper.map_code("IBM.CH", BlueBorderGlyphCodes.RIGHT_PROMPT_IBM_FONT_ID.value).overlay_with(
            overlay = right_prompt_overlay,
            transparent_mapped_rgb = self._color_black
        )

        # Whatever we achieved above, make a left-pointing version of that.
        border_glyphs.left_prompt_glyph = border_glyphs.right_prompt_glyph.rotate_90().rotate_90()

        return border_glyphs
    