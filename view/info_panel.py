from typing import Iterable
from dark_libraries.dark_math import Coord, Rect, Size, Vector2

from data.global_registry import GlobalRegistry

from models.u5_glyph import U5Glyph
from services.font_mapper import FontMapper

from view.display_config      import DisplayConfig
from view.scalable_component  import ScalableComponent

# This is the OG game's info panel width
# NOT THE SAME as the border widths, which will be the INFO_PANEL.w in display_config
ORIGINAL_PANEL_WIDTH = 15

MAXIMUM_NAME_LENGTH = 8
MAXIMUM_PARTY_SIZE = 6

FOOD_GOLD_HEIGHT = 2

# Excludes any top or left borders.
START_X, START_Y = 0, 1

MIDDLE_BORDER_Y = START_Y + MAXIMUM_PARTY_SIZE
BOTTOM_BORDER_Y = START_Y + MAXIMUM_PARTY_SIZE + 1 + FOOD_GOLD_HEIGHT

# scroll

SCROLL_RECT = Rect(
    (START_X, START_Y),
    (ORIGINAL_PANEL_WIDTH, MAXIMUM_PARTY_SIZE + FOOD_GOLD_HEIGHT + 1)
)

SCROLL_CONTENT_RECT = Rect(
    (SCROLL_RECT.x + 1, SCROLL_RECT.y + 1),
    (SCROLL_RECT.w - 2, SCROLL_RECT.h - 2)
)

# Split

TOP_CONTENT_SPLIT_RECT = Rect(
    (START_X, START_Y),
    (ORIGINAL_PANEL_WIDTH, MAXIMUM_PARTY_SIZE)
)

BOTTOM_CONTENT_RECT = Rect(
    (START_X, START_Y + MAXIMUM_PARTY_SIZE + 1),
    (ORIGINAL_PANEL_WIDTH, FOOD_GOLD_HEIGHT)
)

# neither (max capacity)
UNSPLIT_UNSCROLL_CONTENT_RECT = SCROLL_RECT

class InfoPanel(ScalableComponent):

    display_config:  DisplayConfig
    global_registry: GlobalRegistry
    font_mapper:     FontMapper

    def __init__(self):

        self.set_glyph_rows_top([])
        self.set_glyph_rows_bottom([])
        self.set_highlighted_item(None)

        self.set_panel_title(None)
        self.set_middle_status_icon(None)
        self.set_bottom_status_icon(None)

    def _after_inject(self):
        super().__init__(self.display_config.INFO_PANEL_SIZE * self.display_config.FONT_SIZE, self.display_config.SCALE_FACTOR)
        super()._after_inject()

    def set_highlighted_item(self, item_index: int):
        self._highlighted_item_index = item_index

    def set_glyph_rows_top(self, glyph_rows: list[list[U5Glyph]]):
        assert not any([glyph is None for row in glyph_rows for glyph in row]), "Cannot print NULL glyphs"
        self._glyph_rows_top = glyph_rows

    def set_glyph_rows_bottom(self, glyph_rows: list[list[U5Glyph]]):
        assert not any([glyph is None for row in glyph_rows for glyph in row]), "Cannot print NULL glyphs"
        self._glyph_rows_bottom = glyph_rows

    def set_context_party_member(self, party_member_index: int):
        self._context_party_member_index = party_member_index

    def set_panel_geometry(self, 
                                split:  bool = False, 
                                scroll: bool = False
                          ):
        assert not (split and scroll), "split and scroll cannot be used together"

        self._split  = split
        self._scroll = scroll

        if split:
            self._top_content_rect = TOP_CONTENT_SPLIT_RECT
            self._bottom_content_rect = BOTTOM_CONTENT_RECT

        elif scroll:
            self._top_content_rect = SCROLL_CONTENT_RECT
            self._bottom_content_rect = None

        else:
            self._top_content_rect = UNSPLIT_UNSCROLL_CONTENT_RECT
            self._bottom_content_rect = None
            
        self.get_input_surface().fill((0,0,0))

    def _create_border_inset(self, glyphs: Iterable[U5Glyph]) -> Iterable[U5Glyph]:
        if glyphs is None:
            return None
        
        return (
                [self.global_registry.blue_border_glyphs.right_prompt_glyph]
                +
                glyphs
                +
                [self.global_registry.blue_border_glyphs.left_prompt_glyph]
        )

    def set_panel_title(self, title: str):
        if title is None:
            self._panel_title_glyphs = None
            return
        self._panel_title_glyphs = self._create_border_inset(self.font_mapper.map_ascii_string(title))

    def set_middle_status_icon(self, glyph_key: tuple[str, int]):
        if glyph_key is None:
            self._middle_icon_glyphs = None
            return
        self._middle_icon_glyphs = self._create_border_inset(self.global_registry.font_glyphs.get(glyph_key))

    def set_bottom_status_icon(self, glyph_key: tuple[str, int]):
        if glyph_key is None:
            self._bottom_icon_glyphs = None
            return
        self._bottom_icon_glyphs = self._create_border_inset(self.global_registry.font_glyphs.get(glyph_key))

    # This ignores all cursor state and just plasters the glyphs at the given coord.
    # It will not wrap, scroll, or update any state.
    def _print_glyphs_at(self, glyphs: Iterable[U5Glyph], char_coord: Coord, vertikal = False):
        target = self.get_input_surface()
        direction = Vector2(1, 0)
        if vertikal:
            direction = Vector2(0,1)
        for glyph in glyphs:
            glyph.blit_to_surface(char_coord, target)
            char_coord = char_coord + direction

    def _draw_border(self, y: int, border_glyphs: Iterable[U5Glyph], inset_glyphs: Iterable[U5Glyph]):
        self._print_glyphs_at(border_glyphs, Coord(0, y))
        if inset_glyphs:
            x = (ORIGINAL_PANEL_WIDTH // 2) - (len(inset_glyphs) // 2)
            self._print_glyphs_at(inset_glyphs, Coord(x, y))

    def _draw_top_border(self):
        self._draw_border(y = 0, border_glyphs = self._top_border_glyphs, inset_glyphs = self._panel_title_glyphs)

    def _draw_middle_border(self):
        self._draw_border(y = MIDDLE_BORDER_Y, border_glyphs = self._border_glyphs, inset_glyphs = self._middle_icon_glyphs)

    def _draw_bottom_border(self):
        y = self.display_config.INFO_PANEL_SIZE.h - 1
        self._draw_border(y = BOTTOM_BORDER_Y, border_glyphs = self._border_glyphs, inset_glyphs = self._bottom_icon_glyphs)

    def _draw_scroll(self):
        x, y, w, h = SCROLL_RECT.to_tuple() 
        left, top, right, bottom = x, y, x + w - 1, y + h - 1

        self._print_glyphs_at(self._scroll_top,    Coord(left , top    )                 )
        self._print_glyphs_at(self._scroll_side,   Coord(left , top + 1), vertikal = True) # left
        self._print_glyphs_at(self._scroll_side,   Coord(right, top + 1), vertikal = True) # right
        self._print_glyphs_at(self._scroll_bottom, Coord(left , bottom )                 )

    def init(self):
        # Cache a bunch of useful glyph sequences.
        self._top_border_glyphs = [
            self.global_registry.blue_border_glyphs.top_block_glyph
            for _ in range(self.display_config.INFO_PANEL_SIZE.w)
        ]
        self._border_glyphs = [
            self.global_registry.blue_border_glyphs.horizontal_block
            for _ in range(self.display_config.INFO_PANEL_SIZE.w)
        ]
        self._scroll_top = (
            [self.global_registry.scroll_border_glyphs.top_left_cnr_glyph]
            +
            [
                self.global_registry.scroll_border_glyphs.top_block_glyph
                for _ in range(SCROLL_RECT.w - 2)
            ]
            +
            [self.global_registry.scroll_border_glyphs.top_right_cnr_glyph]
        )
        self._scroll_bottom = (
            [self.global_registry.scroll_border_glyphs.bottom_left_cnr_glyph]
            +
            [
                self.global_registry.scroll_border_glyphs.bottom_block_glyph
                for _ in range(SCROLL_RECT.w - 2)
            ]
            +
            [self.global_registry.scroll_border_glyphs.bottom_right_cnr_glyph]
        )
        self._scroll_side = [
            self.global_registry.scroll_border_glyphs.vertical_block
            for _ in range(SCROLL_RECT.h - 2)
        ]

    def draw(self):

        self._draw_top_border()

        if self._scroll:
            self._draw_scroll()

        # top content
        for index, glyph_row in enumerate(self._glyph_rows_top):
            if index == self._highlighted_item_index:
                glyph_row = [glyph.invert_colors() for glyph in glyph_row]
            self._print_glyphs_at(glyph_row, self._top_content_rect.minimum_corner + Vector2(0, index))

        if self._split:
            # bottom content
            for index, glyph_row in enumerate(self._glyph_rows_bottom):
                self._print_glyphs_at(glyph_row, self._bottom_content_rect.minimum_corner + Vector2(0, index))

            self._draw_middle_border()

        self._draw_bottom_border()

