import math
import pygame, base64

from dark_libraries.dark_math import Size

from data.global_registry import GlobalRegistry
from data.loaders.tileset_loader import TileLoader
from data.loaders.u5_font_loader import U5FontLoader
from data.loaders.u5_glyph_loader import U5GlyphLoader
from models.tile import Tile
from models.u5_glyph import U5Glyph
from services.surface_factory import SurfaceFactory
from view.display_config import DisplayConfig

display_config = DisplayConfig()

surface_factory = SurfaceFactory()
surface_factory.display_config = display_config
surface_factory._after_inject()

MARGIN = 10  # padding around grid

class ViewerProfile[TKey, TValue]:

    def __init__(self, dropdown_label):
        self.dropdown_label = dropdown_label
        self.active_row: int = 0
        self.active_col: int = 0
        self.current_scale_factor = self.default_scale_factor()

        self.window_size: Size = None
        self.screen: pygame.Surface = None
        self.button_rect: pygame.Rect = None
        self.dropdown_rect: pygame.Rect = None

    def default_scale_factor(self) -> int:
        return 2

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
            self.viewer_size().w * display_config.TILE_SIZE.w * display_config.SCALE_FACTOR + MARGIN * 2,
            self.viewer_size().h * display_config.TILE_SIZE.h * display_config.SCALE_FACTOR + MARGIN * 2 + 200
        )

        for profile in profiles:
            # Dispose of old screen surfaces.
            profile.screen = None

        self.screen = pygame.display.set_mode(self.window_size.to_tuple())
        pygame.display.set_caption(f"Object Viewer: {self.dropdown_label}")

        margin_bottom_y = MARGIN + active_profile.viewer_size().h * active_profile.object_scaled_size().h + 5

        # Key text label geometry
        self.key_text_coord = (MARGIN, margin_bottom_y)

        # Button geometry
        button_size = Size(100, 24)
        self.button_rect = pygame.Rect(
            self.window_size.w - button_size.w - MARGIN, 
            margin_bottom_y, 
            button_size.w, 
            button_size.h
        )

        # Dropdown geometry
        dropdown_size = Size(120, 24)
        self.dropdown_rect = pygame.Rect(
            MARGIN + 100, 
            margin_bottom_y, 
            dropdown_size.w, 
            dropdown_size.h
        )


class TileViewerProfile(ViewerProfile[int, Tile]):
    def __init__(self):
        super().__init__("TILES.16")
        self.global_registry = GlobalRegistry()

        tile_loader = TileLoader()
        tile_loader.display_config  = display_config
        tile_loader.global_registry = self.global_registry
        tile_loader.surface_factory = surface_factory

        tile_loader.load_tiles()

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
        return 4

    # in un-scaled pixels
    def object_size(self) -> Size:
        return display_config.FONT_SIZE

    # size is in objects, not pixels.
    def viewer_size(self) -> Size:
        width = 32
        return Size(width, math.ceil(self.object_count() / width))
    
    def object_count(self) -> int:
        return 128

    def get_unscaled_object_surface(self, object_index: int) -> pygame.Surface:
        glyph: U5Glyph = self.global_registry.font_glyphs.get((self.font_name, object_index))
        if glyph:
            return glyph.get_surface()
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
        
pygame.init()
pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

profiles = list[ViewerProfile]([
    TileViewerProfile(),
    FontViewerProfile("IBM.CH"),
    FontViewerProfile("RUNES.CH")
])

active_profile = profiles[0]
active_profile.initialise_components()

pygame.scrap.init()

font = pygame.font.SysFont(None, 20)

dropdown_open = False
running = True

# Update the active index.
active_index = active_profile.active_row * active_profile.viewer_size().w + active_profile.active_col

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RIGHT:
                active_profile.active_col = (active_profile.active_col + 1) % active_profile.viewer_size().w # GRID_COLS
            elif event.key == pygame.K_LEFT:
                active_profile.active_col = (active_profile.active_col - 1) % active_profile.viewer_size().w # GRID_COLS
            elif event.key == pygame.K_DOWN:
                active_profile.active_row = (active_profile.active_row + 1) % active_profile.viewer_size().h # GRID_ROWS
            elif event.key == pygame.K_UP:
                active_profile.active_row = (active_profile.active_row - 1) % active_profile.viewer_size().h # GRID_ROWS

            # Update the active index.
            active_index = active_profile.active_row * active_profile.viewer_size().w + active_profile.active_col

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if active_profile.button_rect.collidepoint(event.pos):
                base64_ascii = active_profile.base64(active_index)
                pygame.scrap.put(pygame.SCRAP_TEXT, base64_ascii.encode("utf-8"))
                print(f"Copied object {active_index} to clipboard (base64)")
                    
            elif active_profile.dropdown_rect.collidepoint(event.pos):
                dropdown_open = not dropdown_open
            
            elif dropdown_open:
                # clicked inside dropdown options
                for i, profile in enumerate(profiles):
                    option_rect = pygame.Rect(
                        active_profile.dropdown_rect.x, 
                        active_profile.dropdown_rect.y + (i + 1) * active_profile.dropdown_rect.h, 
                        active_profile.dropdown_rect.w, 
                        active_profile.dropdown_rect.h
                    )
                    if option_rect.collidepoint(event.pos):
                        active_profile = profile
                        active_profile.initialise_components()
                        dropdown_open = False


    active_profile.screen.fill((30, 30, 30))

    # Draw objects in grid
    for row in range(active_profile.viewer_size().h):
        for col in range(active_profile.viewer_size().w):

            x = MARGIN + col * active_profile.object_scaled_size().w
            y = MARGIN + row * active_profile.object_scaled_size().h

            object_index = row * active_profile.viewer_size().w + col

            # For invalid object_index, get's ignored, or can choose to draw a "blank" tile.
            object_surface = active_profile.get_scaled_object_surface(object_index)
            if object_surface:
                active_profile.screen.blit(object_surface, (x, y))

    # Cursor rectangle
    cursor_x = MARGIN + active_profile.active_col * active_profile.object_scaled_size().w
    cursor_y = MARGIN + active_profile.active_row * active_profile.object_scaled_size().h
    cursor_rect = pygame.Rect(
        cursor_x, cursor_y, active_profile.object_scaled_size().w, active_profile.object_scaled_size().h
    )
    pygame.draw.rect(active_profile.screen, (255, 0, 0), cursor_rect, width=3)

    text_surf = font.render(
        f"Key: {active_profile.object_label(active_index)}", 
        True, # antialias
        (255, 255, 255)
    )
    active_profile.screen.blit(text_surf, active_profile.key_text_coord)

    # --- Draw dropdown ---
    # Draw the closed dropdown box
    pygame.draw.rect(active_profile.screen, (50, 50, 50), active_profile.dropdown_rect)
    pygame.draw.rect(active_profile.screen, (200, 200, 200), active_profile.dropdown_rect, 2)

    # Label for the currently active profile
    label = font.render(active_profile.dropdown_label, True, (255, 255, 255))
    active_profile.screen.blit(label, (active_profile.dropdown_rect.x + 5,
                                    active_profile.dropdown_rect.y + 5))

    # If dropdown is open, draw the options
    if dropdown_open:
        for i, profile in enumerate(profiles):
            option_rect = pygame.Rect(
                active_profile.dropdown_rect.x,
                active_profile.dropdown_rect.y + (i + 1) * active_profile.dropdown_rect.h,
                active_profile.dropdown_rect.w,
                active_profile.dropdown_rect.h
            )
            pygame.draw.rect(active_profile.screen, (70, 70, 70), option_rect)
            pygame.draw.rect(active_profile.screen, (200, 200, 200), option_rect, 1)
            opt_label = font.render(profile.dropdown_label, True, (255, 255, 255))
            active_profile.screen.blit(opt_label, (option_rect.x + 5, option_rect.y + 5))

    # Draw copy button
    pygame.draw.rect(active_profile.screen, (0, 0, 0), active_profile.button_rect)
    pygame.draw.rect(active_profile.screen, (255, 0, 0), active_profile.button_rect, width=2)
    btn_label = font.render("Copy Base64", True, (255, 255, 255))
    label_rect = btn_label.get_rect(center=active_profile.button_rect.center)
    active_profile.screen.blit(btn_label, label_rect)

    pygame.display.flip()