from dark_libraries.dark_math import Coord, Size

from data.global_registry import GlobalRegistry
from models.enums.ega_palette_values import EgaPaletteValues

from services.font_mapper import FontMapper
from services.world_clock import CelestialGlyphCodes, WorldClock
from view.info_panel import InfoPanel

from .border_drawer import BorderDrawer
from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

class MainDisplay(ScalableComponent):

    # Injectable
    global_registry: GlobalRegistry
    display_config:  DisplayConfig
    world_clock:     WorldClock
    font_mapper:     FontMapper
    info_panel:      InfoPanel

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
        super()._after_inject()


        self.size_in_glyphs = self._unscaled_size_in_pixels // self.display_config.FONT_SIZE
        tile_to_font_width_ratio = self.display_config.TILE_SIZE.w // self.display_config.FONT_SIZE.w
        self.viewport_width_in_glyphs = self.display_config.VIEW_PORT_SIZE.w * tile_to_font_width_ratio

        # 6 being half the width of the panorama output of 12 chars.
        self.celestial_char_offset = (self.viewport_width_in_glyphs // 2) - 6

        self._color_light_grey = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.LightGrey)
        self._color_yellow     = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.Yellow)
        self._color_white      = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.White)

    def init(self):

        #
        # CELESTIAL GLYPHS
        #

        # The sun and moon phases.  The sun is yellow and the moons are light grey.
        self.celestial_glyphs = {
            celestial_glyph_code.value:
            self.font_mapper.map_code("RUNES.CH", celestial_glyph_code.value).replace_color(
                self._color_white, 
                self._color_yellow if celestial_glyph_code == CelestialGlyphCodes.SUN else self._color_light_grey
            )
            for celestial_glyph_code in CelestialGlyphCodes
        }

        # A blank space.
        self.celestial_glyphs[0] = self.font_mapper.map_code("IBM.CH", CelestialGlyphCodes.BLANK.value)
        
        # The borders only need to be drawn once.
        self.draw_borders()

    def draw_borders(self):
        
        drawer = BorderDrawer(self.global_registry.blue_border_glyphs, self.get_input_surface())

        char_x_middle = self.viewport_width_in_glyphs + 1
        char_x_right  = self.size_in_glyphs.w - 1

        char_y_info_panel = self.display_config.INFO_PANEL_SIZE.h
        char_y_bottom = self.size_in_glyphs.h - 1

        # Blue borders - vertical
        y_range_full = list(range(self.size_in_glyphs.h))
        drawer.left      (            0, y_range_full)
        drawer.right     ( char_x_right, y_range_full)
        drawer.horizontal(char_x_middle, y_range_full) # the glyph is horizontal, the line is vertical

        # Blue borders - horizontal
        x_range_full = list(range(self.size_in_glyphs.w))
        drawer.top   (x_range_full,             0)
        drawer.bottom(x_range_full, char_y_bottom)

#        x_range_middle_to_right = list(range(char_x_middle, char_x_right))
#        drawer.vertical(x_range_middle_to_right, char_y_info_panel) # the glyph is vertical, the line is horizontal

        # corners
        drawer.top_left    (           0,             0)
        drawer.top_right   (char_x_right,             0)
        drawer.bottom_left (           0, char_y_bottom)
        drawer.bottom_right(char_x_right, char_y_bottom)

        # junctions
        drawer.junction(char_x_middle,                  0 )
        drawer.junction(char_x_middle,      char_y_bottom )
        drawer.right   (char_x_middle, [char_y_info_panel])
        drawer.junction(char_x_right ,  char_y_info_panel )

        if self.info_panel.split_info_panel:
            drawer.right   (char_x_middle, [char_y_info_panel - 3])
            drawer.junction(char_x_right ,  char_y_info_panel - 3 )

        # prompts - celestial
        drawer.right_prompt(self.celestial_char_offset, 0)
        drawer.left_prompt(self.viewport_width_in_glyphs - self.celestial_char_offset + 1, 0)

        # prompts - wind direction
        drawer.right_prompt(self.celestial_char_offset + 1, char_y_bottom)
        drawer.left_prompt(self.viewport_width_in_glyphs - self.celestial_char_offset + 1, char_y_bottom)

    def draw_celestial_panorama(self):

        surf = self.get_input_surface()

        # Sun and moons

        for cursor, glyph_code in enumerate(self.world_clock.get_celestial_panorama()):
            glyph = self.celestial_glyphs[glyph_code]
            glyph.blit_to_surface(Coord(self.celestial_char_offset + cursor + 1, 0), surf)

    def draw_wind_direction(self):
        surf = self.get_input_surface()
        char_y_bottom = self.size_in_glyphs.h - 1

        for cursor, glyph in enumerate(self.font_mapper.map_ascii_string("East  Winds")):
            glyph.blit_to_surface(Coord(self.celestial_char_offset + cursor + 2, char_y_bottom), surf)

    def draw(self):
        self.draw_celestial_panorama()
        self.draw_wind_direction()

