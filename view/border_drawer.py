import pygame

from typing import Iterable

from dark_libraries.dark_math import Coord
from models.border_glyphs import BorderGlyphs
from models.u5_glyph import U5Glyph

class BorderDrawer:
    def __init__(self, border_glyphs: BorderGlyphs, target_surface: pygame.Surface):
        self._glyphs = border_glyphs
        self._target_surface = target_surface

    def _blit_at(self, glyph: U5Glyph, x: int, y: int):
        glyph.blit_to_surface(Coord[int](x, y), self._target_surface)

    def _blit(self, glyph: U5Glyph, coords: Iterable[tuple[int,int]]):
        for coord in coords:
            x, y = coord
            self._blit_at(glyph, x, y)

    def left(self, x: int, y_range: Iterable[int]):
        self._blit(
            self._glyphs.left_block_glyph,
            [(x,y) for y in y_range]
        )

    def right(self, x: int, y_range: Iterable[int]):
        self._blit(
            self._glyphs.right_block_glyph,
            [(x,y) for y in y_range]
        )

    def vertical(self, x: int, y_range: Iterable[int]):
        self._blit(
            self._glyphs.vertical_block,
            [(x,y) for y in y_range]
        )

    def top(self, x_range: range, y: int):
        self._blit(
            self._glyphs.top_block_glyph,
            [(x,y) for x in x_range]
        )

    def bottom(self, x_range: range, y: int):
        self._blit(
            self._glyphs.bottom_block_glyph,
            [(x,y) for x in x_range]
        )

    def horizontal(self, x_range: range, y: int):
        self._blit(
            self._glyphs.horizontal_block,
            [(x,y) for x in x_range]
        )

    def top_left(self, x: int, y: int):
        self._blit_at(self._glyphs.top_left_cnr_glyph, x, y)

    def top_right(self, x: int, y: int):
        self._blit_at(self._glyphs.top_right_cnr_glyph, x, y)

    def bottom_left(self, x: int, y: int):
        self._blit_at(self._glyphs.bottom_left_cnr_glyph, x, y)

    def bottom_right(self, x: int, y: int):
        self._blit_at(self._glyphs.bottom_right_cnr_glyph, x, y)

    def junction(self, x: int, y: int):
        self._blit_at(self._glyphs.junction_glyph, x, y)

    def left_prompt(self, x: int, y: int):
        self._blit_at(self._glyphs.left_prompt_glyph, x, y)

    def right_prompt(self, x: int, y: int):
        self._blit_at(self._glyphs.right_prompt_glyph, x, y)

    def draw_glyph(self, glyph: U5Glyph, x: int, y: int):
        self._blit_at(glyph, x, y)