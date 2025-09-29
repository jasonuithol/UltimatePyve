from dark_libraries.dark_math import Size

class EgaPalette(list[tuple[int,int,int]]):
    pass

class DisplayConfig:

    # ===================================================================================================
    # =============== Section 1: Don't change these unless you know what you're doing ===================
    # ===================================================================================================

    TARGET_FPS = 144
    SCALE_FACTOR = 2

    # In theory these should come from their respective realms
    # but it's too much of a pain in the butt to make them that dynamic.
    #
    FONT_SIZE = Size( 8,  8) # in unscaled pixels.
    TILE_SIZE = Size(16, 16) # in unscaled pixels.


    # ================================================================================
    # =============== Section 2: Change these to whatever you like ===================
    # ================================================================================

    VIEW_PORT_SIZE = Size(17, 17) # In tiles       (16x16)
    CONSOLE_SIZE   = Size(32, 13) # In font glyphs (8x8)

    EGA_PALETTE = EgaPalette([
        (0, 0, 0),         # 0000: Black
        (0, 0, 170),       # 0001: Blue
        (0, 170, 0),       # 0010: Green
        (0, 170, 170),     # 0011: Cyan

        (170, 0, 0),       # 0100: Red
        (170, 0, 170),     # 0101: Magenta
        (170, 85, 0),      # 0110: Brown (dark yellow)
        (170, 170, 170),   # 0111: Light Gray

        (85, 85, 85),      # 1000: Dark Gray
        (85, 85, 255),     # 1001: Light Blue
        (85, 255, 85),     # 1010: Light Green
        (85, 255, 255),    # 1011: Light Cyan

        (255, 85, 85),     # 1100: Light Red
        (255, 85, 255),    # 1101: Light Magenta
        (255, 255, 85),    # 1110: Yellow
        (255, 255, 255),   # 1111: White
    ])