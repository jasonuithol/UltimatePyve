import math
import pygame, base64

from dark_libraries.dark_math import Size
from dark_libraries.registry import Registry

from data.global_registry import GlobalRegistry
from data.loaders.location_metadata_builder import LocationMetadataBuilder
from data.loaders.tileset_loader import TileLoader
from data.loaders.u5_font_loader import U5FontLoader
from data.loaders.u5_glyph_loader import U5GlyphLoader
from data.loaders.u5_map_loader import U5MapLoader

from models.data_ovl import DataOVL
from models.tile import Tile
from models.u5_glyph import U5Glyph
from models.u5_map_level import U5MapLevel

from services.surface_factory import SurfaceFactory

from view.display_config import DisplayConfig

display_config = DisplayConfig()

surface_factory = SurfaceFactory()
surface_factory.display_config = display_config
surface_factory._after_inject()

data_ovl = DataOVL.load()

tile_loader = TileLoader()
tile_loader.display_config  = display_config
tile_loader.global_registry = GlobalRegistry()
tile_loader.surface_factory = surface_factory

tile_loader.load_tiles()

MARGIN = 20  # padding around grid


# Inherit from this to make a custom profile type
class ViewerProfile[TKey, TValue]:

    def __init__(self, dropdown_label):
        self.dropdown_label = dropdown_label
        self.active_row: int = 0
        self.active_col: int = 0
        self.scroll_row: int = 0
        self.current_scale_factor = self.default_scale_factor()

        self.window_size: Size = None
        self.screen: pygame.Surface = None
        self.button_rect: pygame.Rect = None
        self.dropdown_rect: pygame.Rect = None

    def get_active_index(self) -> int:
        return (self.scroll_row + self.active_row) * self.viewer_size().w + self.active_col

    def default_scale_factor(self) -> float:
        return 2.0

    # in un-scaled pixels
    def object_size(self) -> Size:
        ...

    def object_scaled_size(self) -> Size:
        return self.object_size().scale(self.current_scale_factor)

    # size is in objects, not pixels.
    def viewer_size(self) -> Size:
        ...

    def object_count(self) -> int:
        ...

    def get_unscaled_object_surface(self, object_index: int) -> pygame.Surface:
        ...

    def get_scaled_object_surface(self, object_index: int) -> pygame.Surface:
        unscaled_surface = self.get_unscaled_object_surface(object_index)
        if unscaled_surface:
            return pygame.transform.scale(
                unscaled_surface,
                (self.object_size() * self.current_scale_factor).to_tuple()
            )
        else:
            return None

    def object_label(self, object_index: int) -> str:
        if object_index < self.object_count():
            return str(object_index)
        else:
            return "n/a"
    
    # Returns ASCII string
    def base64(self, object_index: int) -> str:
        ...

    def initialise_components(self):

        self.window_size = Size(
            self.viewer_size().w * self.object_scaled_size().w + MARGIN * 2,
            self.viewer_size().h * self.object_scaled_size().h + MARGIN * 2
        )

        self.screen = pygame.display.set_mode(self.window_size.to_tuple())
        pygame.display.set_caption(f"Object Viewer: (initialising)")

class TileViewerProfile(ViewerProfile[int, Tile]):
    def __init__(self):
        super().__init__("TILES.16")
        self.global_registry = tile_loader.global_registry

        print(f"Loaded {__class__.__name__} as {self.dropdown_label}")

    def default_scale_factor(self) -> int:
        return 2

    # in un-scaled pixels
    def object_size(self) -> Size:
        return display_config.TILE_SIZE

    # size is in objects, not pixels.
    def viewer_size(self) -> Size:
        width = 32
        return Size(width, math.ceil(self.object_count() / width))
    
    def object_count(self) -> int:
        return len(self.global_registry.tiles)

    def get_unscaled_object_surface(self, object_index: int) -> pygame.Surface:
        tile = self.global_registry.tiles.get(object_index)
        if tile:
            return tile.get_surface()
        else:
            return None
    
    # Returns ASCII string
    def base64(self, object_index: int) -> str:
        tile = self.global_registry.tiles.get(object_index)
        if tile:
            flat_bytes = bytes([pix for row in tile.pixels for pix in row])
            return base64.b64encode(flat_bytes).decode("ascii")
        else:
            return ""

class FontViewerProfile(ViewerProfile[tuple[str,int], U5Glyph]):
    def __init__(self, font_name):
        super().__init__(font_name)
        self.font_name = font_name
        self.global_registry = GlobalRegistry()

        f_loader = U5FontLoader()
        f_loader.global_registry = self.global_registry
        f_loader.register_fonts()

        g_loader = U5GlyphLoader()
        g_loader.display_config = display_config
        g_loader.global_registry = self.global_registry
        g_loader.surface_factory = surface_factory
        g_loader.register_glyphs()

        print(f"Loaded {__class__.__name__} as {self.dropdown_label}")

    def default_scale_factor(self) -> int:
        return 8

    # in un-scaled pixels
    def object_size(self) -> Size:
        return display_config.FONT_SIZE

    # size is in objects, not pixels.
    def viewer_size(self) -> Size:
        width = 16
        return Size(width, math.ceil(self.object_count() / width))
    
    def object_count(self) -> int:
        return 128

    def get_unscaled_object_surface(self, object_index: int) -> pygame.Surface:
        glyph: U5Glyph = self.global_registry.font_glyphs.get((self.font_name, object_index))
        if glyph:
            return glyph.get_surface()
        else:
            return None
    
    def get_scaled_object_surface(self, object_index: int) -> pygame.Surface:
        unscaled_surface = self.get_unscaled_object_surface(object_index)
        if unscaled_surface:
            scaled_surface = pygame.transform.scale(
                unscaled_surface,
                (self.object_size() * self.current_scale_factor).to_tuple()
            )

            grid_color_major = (0, 255, 0)
            grid_color_minor = (0, 128, 0)

            for x in range(self.current_scale_factor, self.object_scaled_size().w, self.current_scale_factor):
                pygame.draw.line(scaled_surface, grid_color_minor, (x, 0), (x, self.object_scaled_size().h))

            for y in range(self.current_scale_factor, self.object_scaled_size().h, self.current_scale_factor):
                pygame.draw.line(scaled_surface, grid_color_minor, (0, y), (self.object_scaled_size().w, y))

            pygame.draw.line(scaled_surface, grid_color_major, (0, 0), (0, self.object_scaled_size().h))
            pygame.draw.line(scaled_surface, grid_color_major, (0, 0), (self.object_scaled_size().w, 0))

            return scaled_surface
        else:
            return None
        
    # Returns ASCII string
    def base64(self, object_index: int) -> str:

        font = self.global_registry.fonts.get(self.font_name)
        if not font:
            return ""

        if not object_index < self.object_count():
            return ""

        data = font[object_index]
        flat_bytes = bytes([pix for row in data[object_index] for pix in row])
        return base64.b64encode(flat_bytes).decode("ascii")
        
class MapViewerProfile(ViewerProfile[tuple[str,int], U5MapLevel]):
    def __init__(self, tile_set: Registry[int, Tile]):
        if tile_set:
            option_label = "Maps With Tiles"
        else:
            option_label = "Maps (raw)"

        super().__init__(option_label)
        self.global_registry = GlobalRegistry()
        self.tile_set = tile_set

        loader = U5MapLoader()
        loader.builder = LocationMetadataBuilder()
        loader.builder.dataOvl = data_ovl
        loader.global_registry = self.global_registry
        loader.data_ovl = data_ovl

        loader._after_inject()
        loader.register_maps()
        
        level_tuples = [
            (level_index,  map_)
            for map_ in self.global_registry.maps.values()
            for level_index in map_.get_level_indexes()
        ]

        self.map_levels = {
            object_index : level_tuple
            for object_index, level_tuple in enumerate(level_tuples)
        }

        if tile_set:
            # If the maps are too big, make this fraction even smaller (optional: for maximum crispness make the denominator a factor of 2 i.e. 1/16, 1/32)
            self.current_scale_factor = 1/8
            tile_size = 16
        else:
            self.current_scale_factor = 1
            tile_size = 1

        maximum_map_size = Size(
            max(map.get_size().w for map in self.global_registry.maps.values()),
            max(map.get_size().h for map in self.global_registry.maps.values())
        )

        self._object_size = maximum_map_size * tile_size

        print(f"Maximum map object size unscaled={self.object_size()}, scaled={self.object_scaled_size()}")

        desktop_sizes = pygame.display.get_desktop_sizes()
        self.primary_display_size = desktop_sizes[0]
        print(f"Using primary display size of {self.primary_display_size[0]}x{self.primary_display_size[1]} pixels")

        print(f"Map viewer size in objects is {self.viewer_size()}")

        print(f"Loaded {__class__.__name__} as {self.dropdown_label}")

    def default_scale_factor(self) -> int:
        return 1

    # in un-scaled pixels
    def object_size(self) -> Size:
        return self._object_size

    # size is in objects, not pixels.
    def viewer_size(self) -> Size:
        width  = max(self.primary_display_size[0] // self.object_scaled_size().w, 1)
        height = max((self.primary_display_size[1] - 100) // self.object_scaled_size().h, 1)
        return Size(width, height)
    
    def object_count(self) -> int:
        return len(self.map_levels)

    def get_unscaled_object_surface(self, object_index: int) -> pygame.Surface:
        if object_index < self.object_count():
            level_index, map_ = self.map_levels[object_index]
            return map_.get_map_level(level_index).render_to_surface(tiles = self.tile_set)
        else:
            return None
    
    def object_label(self, object_index: int) -> str:
        if object_index < self.object_count():
            level_index, map_ = self.map_levels[object_index]
            return f"{map_.name} ({map_.location_index},{level_index})"
        else:
            return "n/a"
        
    # Returns ASCII string
    def base64(self, object_index: int) -> str:
        if not object_index < self.object_count():
            return ""

        level_index, map_ = self.map_levels[object_index]
        map_level = map_.get_map_level(level_index)

        data = map_level._data
        flat_bytes = bytes(color for color in data.values())
        return base64.b64encode(flat_bytes).decode("ascii")