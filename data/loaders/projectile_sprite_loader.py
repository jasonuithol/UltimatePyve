from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.enums.projectile_type import ProjectileType
from models.glyph_key import GlyphKey
from models.sprite import Sprite
from models.u5_glyph import U5Glyph

class ProjectileSpriteLoader(LoggerMixin):

    global_registry: GlobalRegistry

    def load(self):
        #
        # Throwing Axe
        #
        axe1 = self.global_registry.font_glyphs.get(GlyphKey(font_name = "RUNES.CH", glyph_code = 9))
        axe2 = axe1.rotate_90()
        axe3 = axe2.rotate_90()
        axe4 = axe3.rotate_90()
        frames = list[U5Glyph]([axe1,axe2,axe3,axe4])
        for f in frames:
            f.get_surface().set_colorkey((0,0,0))

        axe_sprite = Sprite(frames, frame_duration_seconds = 0.025)
        self.global_registry.projectile_sprites.register(ProjectileType.ThrowingAxe, axe_sprite)

        #
        # Fireball
        #
        
