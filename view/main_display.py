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
            unscaled_size_in_pixels = Size[int](
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


    def init(self):

        self._color_light_grey = self.global_registry.colors.get(EgaPaletteValues.LightGrey)
        self._color_yellow     = self.global_registry.colors.get(EgaPaletteValues.Yellow)
        self._color_white      = self.global_registry.colors.get(EgaPaletteValues.White)

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

        assert self.global_registry.blue_border_glyphs.vertical_block, "Must have a vertical_block"
        self.drawer = BorderDrawer(self.global_registry.blue_border_glyphs, self.get_input_surface())


        self.char_x_middle = self.viewport_width_in_glyphs + 1
        self.char_x_right  = self.size_in_glyphs.w - 1

        self.char_y_info_panel = self.display_config.INFO_PANEL_SIZE.h
        self.char_y_bottom = self.size_in_glyphs.h - 1

        # Blue borders - horizontal
        self.y_range_full = list(range(self.size_in_glyphs.h))

        # The borders only need to be drawn once.
        self.draw_borders()

    def draw_borders(self):
        drawer = self.drawer

        drawer.left      (                 0, self.y_range_full)
        drawer.right     ( self.char_x_right, self.y_range_full)
        drawer.vertical(self.char_x_middle, self.y_range_full) # the glyph is vertical, the line is horizontal

        # Blue borders - vertical
        x_range_full = list(range(self.size_in_glyphs.w))
        drawer.top   (x_range_full,                  0)
        drawer.bottom(x_range_full, self.char_y_bottom)

        # corners
        drawer.top_left    (                0,                  0)
        drawer.top_right   (self.char_x_right,                  0)
        drawer.bottom_left (                0, self.char_y_bottom)
        drawer.bottom_right(self.char_x_right, self.char_y_bottom)

        # junctions
        drawer.junction(self.char_x_middle,                       0 )
        drawer.junction(self.char_x_middle,      self.char_y_bottom )
        drawer.right   (self.char_x_middle, [self.char_y_info_panel - 1])
        drawer.junction(self.char_x_right ,  self.char_y_info_panel - 1)


        # prompts - celestial
        drawer.right_prompt(self.celestial_char_offset, 0)
        drawer.left_prompt(self.viewport_width_in_glyphs - self.celestial_char_offset + 1, 0)

        # prompts - wind direction
        drawer.right_prompt(self.celestial_char_offset + 1, self.char_y_bottom)
        drawer.left_prompt(self.viewport_width_in_glyphs - self.celestial_char_offset + 1, self.char_y_bottom)

    def draw_celestial_panorama(self):

        surf = self.get_input_surface()

        # Sun and moons

        for cursor, glyph_code in enumerate(self.world_clock.get_celestial_panorama()):
            glyph = self.celestial_glyphs[glyph_code]
            glyph.blit_at_char_coord(Coord[int](self.celestial_char_offset + cursor + 1, 0), surf)

    def draw_wind_direction(self):
        surf = self.get_input_surface()
        char_y_bottom = self.size_in_glyphs.h - 1

        for cursor, glyph in enumerate(self.font_mapper.map_ascii_string("East  Winds")):
            glyph.blit_at_char_coord(Coord[int](self.celestial_char_offset + cursor + 2, char_y_bottom), surf)

    def set_info_panel_split_state(self, split: bool):
        self._info_panel_split = split

    def draw(self):
        self.draw_celestial_panorama()
        self.draw_wind_direction()

        if self._info_panel_split:
            self.drawer.right   (self.char_x_middle, [self.char_y_info_panel - 4])
            self.drawer.junction(self.char_x_right ,  self.char_y_info_panel - 4 )
        else:
            self.drawer.vertical(self.char_x_middle, [self.char_y_info_panel - 4])
            self.drawer.right   (self.char_x_right , [self.char_y_info_panel - 4])
