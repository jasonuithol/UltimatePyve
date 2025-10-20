from dark_libraries.dark_math import Size
from models.enums.ega_palette_values import EgaPaletteValues

class EgaPalette(tuple[tuple[int,int,int]]):
    pass

class DisplayConfig:

    # ===================================================================================================
    # =============== Section 1: Don't change these unless you know what you're doing ===================
    # ===================================================================================================

    SCALE_FACTOR = 2

    # In theory these should come from their respective realms
    # but it's too much of a pain in the butt to make them that dynamic.
    #
    FONT_SIZE = Size( 8,  8) # in unscaled pixels.
    TILE_SIZE = Size(16, 16) # in unscaled pixels.


    # ================================================================================
    # =============== Section 2: Change these to whatever you like ===================
    # ================================================================================

    VIEW_PORT_SIZE  = Size(17, 17) # In tiles       (which are themselves 16x16 by default, unless changed in TILE_SIZE)
    INFO_PANEL_SIZE = Size(32, 10) # In font glyphs (which are themselves  8x8  by default, unless changed in FONT_SIZE)
    
    # In font glyphs (which are themselves  8x8  by default, unless changed in FONT_SIZE)
    CONSOLE_SIZE = Size(INFO_PANEL_SIZE.w, VIEW_PORT_SIZE.h * 2 - INFO_PANEL_SIZE.h) 

    #
    # TODO: Right now we do NOT take advantage of the fact we can create 8-bit (or other) surfaces and then provide them a palette, or frankly
    #       any other default configuration.
    #
    #       Currently, we call pygame.Surface.map_rgb(tuple[int,int,int]) each time we need to paint an actual pixel color.
    #       We need a SurfaceFactory, which can produce surfaces guaranteed to be compatable with eachother, have, or not have, palettes, etc.
    #
    EGA_PALETTE = {
        index : color.value 
        for index, color in enumerate(EgaPaletteValues)
    }
