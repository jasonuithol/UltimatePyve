from dark_libraries.dark_math import Size
from data.global_registry import GlobalRegistry
from models.enums.ega_palette_values import EgaPaletteValues
from services.surface_factory import SurfaceFactory

class ColorLoader:

    global_registry: GlobalRegistry
    surface_factory: SurfaceFactory

    def load(self):
        s = self.surface_factory.create_surface(Size[int](1,1))
        for color in EgaPaletteValues:
            self.global_registry.colors.register(color, s.map_rgb(color.value))
