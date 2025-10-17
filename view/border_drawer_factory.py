import pygame

from enum import Enum
from typing import Iterable

from dark_libraries.dark_math import Coord

from models.enums.ega_palette_values import EgaPaletteValues
from models.u5_glyph import U5Glyph

from services.font_mapper import FontMapper
from services.surface_factory import SurfaceFactory

class BorderGlyphCodes(Enum):
    SPACE_IBM_FONT_ID = 0
    RIGHT_PROMPT_IBM_FONT_ID = 2

    BLOCK_GLYPH_IBM_FONT_ID = 127
    TOP_LEFT_CNR_GLYPH_IBM_FONT_ID = 123
    TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID = 124
    BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID = 125
    BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID = 126
    
class BorderDrawer:
    def __init__(self, target_surface: pygame.Surface):
        self._target_surface = target_surface

    def _blit_at(self, glyph: U5Glyph, x: int, y: int):
        glyph.blit_to_surface(Coord(x, y), self._target_surface)

    def _blit(self, glyph: U5Glyph, coords: Iterable[tuple[int,int]]):
        for coord in coords:
            x, y = coord
            self._blit_at(glyph, x, y)

    def left(self, x: int, y_range: Iterable[int]):
        self._blit(
            self.left_block_glyph,
            [(x,y) for y in y_range]
        )

    def right(self, x: int, y_range: Iterable[int]):
        self._blit(
            self.right_block_glyph,
            [(x,y) for y in y_range]
        )

    # The glyph is horizontal.  It's drawn in a vertical line.
    def horizontal(self, x: int, y_range: Iterable[int]):
        self._blit(
            self.horizontal_block,
            [(x,y) for y in y_range]
        )

    def top(self, x_range: range, y: int):
        self._blit(
            self.top_block_glyph,
            [(x,y) for x in x_range]
        )

    def bottom(self, x_range: range, y: int):
        self._blit(
            self.bottom_block_glyph,
            [(x,y) for x in x_range]
        )

    # The glyph is vertical.  It's drawn in a horizontal line.
    def vertical(self, x_range: range, y: int):
        self._blit(
            self.vertical_block,
            [(x,y) for x in x_range]
        )

    def top_left(self, x: int, y: int):
        self._blit_at(self.top_left_cnr_glyph, x, y)

    def top_right(self, x: int, y: int):
        self._blit_at(self.top_right_cnr_glyph, x, y)

    def bottom_left(self, x: int, y: int):
        self._blit_at(self.bottom_left_cnr_glyph, x, y)

    def bottom_right(self, x: int, y: int):
        self._blit_at(self.bottom_right_cnr_glyph, x, y)

    def junction(self, x: int, y: int):
        self._blit_at(self.junction_glyph, x, y)

    def left_prompt(self, x: int, y: int):
        self._blit_at(self.left_prompt_glyph, x, y)

    def right_prompt(self, x: int, y: int):
        self._blit_at(self.right_prompt_glyph, x, y)

class BorderDrawerFactory:

    surface_factory: SurfaceFactory
    font_mapper:     FontMapper

    def create_border_drawer(self, target_surface: pygame.Surface) -> BorderDrawer:

        # Be careful changing these colors.
        self._color_black      = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.Black)
        self._color_white      = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.White)

        # Go nuts changing this color.
        self._color_dark_blue  = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.Blue)

        border_drawer = BorderDrawer(target_surface)

        #
        # BORDER TOP, BOTTOM, LEFT, RIGHT GLYPHS
        #
        border_drawer.right_block_glyph = self.font_mapper.map_code(
            "IBM.CH", 
            BorderGlyphCodes.BLOCK_GLYPH_IBM_FONT_ID.value
        ).replace_color(
            # Set foreground to blue (this is the thick blue border)
            old_mapped_rgb = self._color_white, 
            new_mapped_rbg = self._color_dark_blue
        ).replace_color(
            # Set background to white (this is the thin white border)
            old_mapped_rgb = self._color_black, 
            new_mapped_rbg = self._color_white
        )
        border_drawer.top_block_glyph    = border_drawer.right_block_glyph.rotate_90()
        border_drawer.left_block_glyph   = border_drawer.top_block_glyph.rotate_90()
        border_drawer.bottom_block_glyph = border_drawer.left_block_glyph.rotate_90()

        #
        # BORDER HORIZONTAL, VERTICAL MIDDLE BORDER GLYPHS
        #
        border_drawer.horizontal_block = border_drawer.left_block_glyph.overlay_with(
            overlay                = border_drawer.right_block_glyph, 
            transparent_mapped_rgb = self._color_dark_blue
        )
        border_drawer.vertical_block = border_drawer.horizontal_block.rotate_90()

        #
        # BORDER CORNER GLYPHS
        #

        # This is used to fix a gap between the block borders and the right hand side rounded corner glyphs.
        # Use "self._color_black" as the transparency color when overlaying the target corner glyphs.
        right_cnr_overlay_glyph = self.font_mapper.map_code(
            "IBM.CH", 
            BorderGlyphCodes.BLOCK_GLYPH_IBM_FONT_ID.value
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

        border_drawer.top_left_cnr_glyph     = corner_maker_func(BorderGlyphCodes.TOP_LEFT_CNR_GLYPH_IBM_FONT_ID.value)
        border_drawer.bottom_left_cnr_glyph  = corner_maker_func(BorderGlyphCodes.BOTTOM_LEFT_CNR_GLYPH_IBM_FONT_ID.value)

        # These two will get "fixed" by the overlay we made earlier.
        border_drawer.top_right_cnr_glyph    = corner_maker_func(BorderGlyphCodes.TOP_RIGHT_CNR_GLYPH_IBM_FONT_ID.value).overlay_with(right_cnr_overlay_glyph, self._color_black)
        border_drawer.bottom_right_cnr_glyph = corner_maker_func(BorderGlyphCodes.BOTTOM_RIGHT_CNR_GLYPH_IBM_FONT_ID.value).overlay_with(right_cnr_overlay_glyph, self._color_black)

        # Just a big old block of blue.
        border_drawer.junction_glyph = self.font_mapper.map_code("IBM.CH", BorderGlyphCodes.SPACE_IBM_FONT_ID.value).replace_color(self._color_black, self._color_dark_blue)

        
        #
        # PROMPTS
        #
        # TODO: Still havent quite got this right
        #

        # Make a blue right-pointing rounded triangle, and then shift it left 1 pixel.
        right_prompt_overlay = self.font_mapper.map_code("IBM.CH", BorderGlyphCodes.RIGHT_PROMPT_IBM_FONT_ID.value).replace_color(self._color_white, self._color_dark_blue)
        right_prompt_overlay._surface.scroll(dx = -1, dy = 0)

        # Fetch a default white right-pointing rounded triangle, and then overlay the shifted blue triangle over it, using black as the transparency color.
        # The result is supposed to be a blue triangle with a thin white border.  It almost but not quite works.
        border_drawer.right_prompt_glyph = self.font_mapper.map_code("IBM.CH", BorderGlyphCodes.RIGHT_PROMPT_IBM_FONT_ID.value).overlay_with(
            overlay = right_prompt_overlay,
            transparent_mapped_rgb = self._color_black
        )

        # Whatever we achieved above, make a left-pointing version of that.
        border_drawer.left_prompt_glyph = border_drawer.right_prompt_glyph.rotate_90().rotate_90()

        return border_drawer
    