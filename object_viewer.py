from configure import get_u5_path, check_python_version

check_python_version()
u5_path = get_u5_path()

import math
import pygame

from data.global_registry import GlobalRegistry
from data.loaders.tileset_loader import TileLoader

from models.data_ovl import DataOVL
from services.surface_factory import SurfaceFactory
from view.display_config import DisplayConfig

from object_viewer_lib.object_viewer_menu_bar import ObjectViewerMenuBar
from object_viewer_lib.object_viewer_profiles import FontViewerProfile, MapViewerProfile, TileViewerProfile, ViewerProfile, configure_profiles

pygame.init()
pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
screen = pygame.display.set_mode(
    size  = (100,100),
    flags = pygame.SCALED | pygame.DOUBLEBUF, 
    vsync = 1
)

clock = pygame.time.Clock()

display_config = DisplayConfig()

surface_factory = SurfaceFactory()
surface_factory.display_config = display_config
surface_factory._after_inject()

data_ovl = DataOVL(u5_path)

tile_loader = TileLoader()
tile_loader.display_config  = display_config
tile_loader.global_registry = GlobalRegistry()
tile_loader.surface_factory = surface_factory

tile_loader.load_tiles(u5_path)

MARGIN = 20  # padding around grid

configure_profiles(
    u5_path,
    display_config, 
    surface_factory, 
    data_ovl, 
    tile_loader, 
    MARGIN
)

profiles = list[ViewerProfile]([
    TileViewerProfile(),
    FontViewerProfile("IBM.CH"),
    FontViewerProfile("RUNES.CH"),
    MapViewerProfile(tile_set = None),
    MapViewerProfile(tile_set = tile_loader.global_registry.tiles), # EVIL: A bit evil, at least
])

active_profile = profiles[0]
active_profile.initialise_components()

dropdown_open = False
running = True

# Clipboard Manager
pygame.scrap.init()

font = pygame.font.SysFont(None, 20)

menu_bar = ObjectViewerMenuBar(profiles, font)

while running:
    for event in pygame.event.get():

        go_up = go_down = go_left = go_right = False
        menu_bar.handle_event(event)
        active_profile = menu_bar.active

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RIGHT:
                go_right = True
            elif event.key == pygame.K_LEFT:
                go_left = True
            elif event.key == pygame.K_DOWN:
                go_down = True
            elif event.key == pygame.K_UP:
                go_up = True

        elif event.type == pygame.MOUSEWHEEL:

            mods = pygame.key.get_mods()
            shift_held = mods & (pygame.KMOD_LSHIFT | pygame.KMOD_RSHIFT)

            if shift_held:
                if event.y == 1:
                    go_left = True
                elif event.y == -1:
                    go_right = True
                
            else:
                if event.y == 1:
                    go_up = True
                elif event.y == -1:
                    go_down = True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # left click
            # convert mouse coords to tile indices
            mx, my = event.pos
            col = (mx - MARGIN) // active_profile.object_scaled_size().w
            row = (my - MARGIN) // active_profile.object_scaled_size().h

            # check that a valid tile was clicked and not like the margin or something else.
            if 0 <= col < active_profile.viewer_size().w and 0 <= row < active_profile.viewer_size().h:
                active_profile.active_col = col
                active_profile.active_row = row

                # Copy the key of the object into the clipboard.
                clicked_ix = active_profile.get_active_index()
                if not clicked_ix is None:
                    clicked_key = active_profile.object_label(clicked_ix)
                    if not clicked_key is None:
                        pygame.scrap.put(pygame.SCRAP_TEXT, clicked_key.encode("utf-8"))

        if go_up:
            if active_profile.active_row > 0:
                    active_profile.active_row -= 1
            else:
                # at top of viewport
                if active_profile.scroll_row > 0:
                    active_profile.scroll_row -= 1

        elif go_down:
            if active_profile.active_row < active_profile.viewer_size().h - 1:
                active_profile.active_row += 1
            else:
                # at bottom of viewport
                max_rows = math.ceil(active_profile.object_count() / active_profile.viewer_size().w)
                if active_profile.scroll_row + active_profile.viewer_size().h < max_rows:
                    active_profile.scroll_row += 1

        elif go_left:
            active_profile.active_col = (active_profile.active_col - 1) % active_profile.viewer_size().w # GRID_COLS

        elif go_right:
            active_profile.active_col = (active_profile.active_col + 1) % active_profile.viewer_size().w # GRID_COLS



        pygame.display.set_caption(f"Object Viewer: {active_profile.dropdown_label} | {active_profile.object_label(active_profile.get_active_index())}")

    # ----------------------
    #
    # DRAWING
    #
    # ----------------------

    active_profile.screen.fill((30, 30, 30))

    menu_bar.draw(active_profile.screen)

    # Draw objects in grid
    for row in range(active_profile.viewer_size().h):
        for col in range(active_profile.viewer_size().w):

            x = MARGIN + col * active_profile.object_scaled_size().w
            y = MARGIN + row * active_profile.object_scaled_size().h

            object_index = (active_profile.scroll_row + row) * active_profile.viewer_size().w + col

            # For invalid object_index, get's ignored, or can choose to draw a "blank" tile.
            if object_index < active_profile.object_count():
                object_surface = active_profile.get_scaled_object_surface(object_index)
                if object_surface:
                    active_profile.screen.blit(object_surface, (x, y))

    # Cursor rectangle
    cursor_x = MARGIN + active_profile.active_col * active_profile.object_scaled_size().w
    cursor_y = MARGIN + active_profile.active_row * active_profile.object_scaled_size().h
    cursor_rect = pygame.Rect[int](
        cursor_x, cursor_y, active_profile.object_scaled_size().w, active_profile.object_scaled_size().h
    )
    pygame.draw.rect(active_profile.screen, (255, 0, 0), cursor_rect, width=3)

    pygame.display.flip()
