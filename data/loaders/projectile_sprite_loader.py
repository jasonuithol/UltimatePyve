from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.enums.ega_palette_values import EgaPaletteValues
from models.enums.projectile_type import ProjectileType
from models.glyph_key import GlyphKey
from models.sprite import Sprite
from models.u5_glyph import U5Glyph
from services.surface_factory import SurfaceFactory

class ProjectileSpriteLoader(LoggerMixin):

    global_registry: GlobalRegistry
    surface_factory: SurfaceFactory

    def load(self):
        #
        # Throwing Axe
        #
        axe1 = self.global_registry.font_glyphs.get(GlyphKey(font_name = "RUNES.CH", glyph_code = 9))
        frames = self._spinning_glyph_frames(axe1)
        axe_sprite = Sprite(frames, frame_duration_seconds = 0.025)
        self.global_registry.projectile_sprites.register(ProjectileType.ThrowingAxe, axe_sprite)

        #
        # Magic missile
        #
        mm_sprite = self._ball_of_particles(EgaPaletteValues.Blue)
        self.global_registry.projectile_sprites.register(ProjectileType.MagicMissile, mm_sprite)

        # Finished loading
        self.log(f"Registered {len(self.global_registry.projectile_sprites)} projectile sprites")

    def _ball_of_particles(self, color: EgaPaletteValues) -> Sprite:

        white_mapped = self.global_registry.colors.get(EgaPaletteValues.White)
        color_mapped = self.global_registry.colors.get(color)

        ball = self.global_registry.font_glyphs.get(GlyphKey(font_name = "RUNES.CH", glyph_code = 14))
        frames = self._spinning_glyph_frames(ball)

        frames = [
            f.replace_color(white_mapped, color_mapped)            
            for f in frames
        ]

        sprite = Sprite(frames, frame_duration_seconds = 0.025)
        return sprite

    def _spinning_glyph_frames(self, first_glyph: U5Glyph) -> list[U5Glyph]:

        frame2 = first_glyph.rotate_90()
        frame3 = frame2.rotate_90()
        frame4 = frame3.rotate_90()
        frames = [first_glyph, frame2, frame3, frame4]

        for f in frames:
            f.get_surface().set_colorkey((0,0,0))

        return frames
