import math
import pygame

pygame.init()
pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

# Import ViewerProfiles (AFTER pygame.init())
from object_viewer_profiles import MARGIN, FontViewerProfile, MapViewerProfile, TileViewerProfile, ViewerProfile, tile_loader

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

pygame.scrap.init()
font = pygame.font.SysFont(None, 20)

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
                if active_profile.active_row < active_profile.viewer_size().h - 1:
                    active_profile.active_row += 1
                else:
                    # at bottom of viewport
                    max_rows = math.ceil(active_profile.object_count() / active_profile.viewer_size().w)
                    if active_profile.scroll_row + active_profile.viewer_size().h < max_rows:
                        active_profile.scroll_row += 1

            elif event.key == pygame.K_UP:
                if active_profile.active_row > 0:
                        active_profile.active_row -= 1
                else:
                    # at top of viewport
                    if active_profile.scroll_row > 0:
                        active_profile.scroll_row -= 1

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if active_profile.button_rect.collidepoint(event.pos):
                base64_ascii = active_profile.base64(active_profile.get_active_index())
                pygame.scrap.put(pygame.SCRAP_TEXT, base64_ascii.encode("utf-8"))
                print(f"Copied object {active_profile.get_active_index()} to clipboard (base64)")
                    
            elif active_profile.dropdown_rect.collidepoint(event.pos):
                dropdown_open = not dropdown_open
            
            elif dropdown_open:
                # clicked inside dropdown options
                clicked_profile: ViewerProfile = None
                for i, profile in enumerate(profiles):
                    option_rect = pygame.Rect(
                        active_profile.dropdown_rect.x, 
                        active_profile.dropdown_rect.y + (i + 1) * active_profile.dropdown_rect.h, 
                        active_profile.dropdown_rect.w, 
                        active_profile.dropdown_rect.h
                    )
                    if option_rect.collidepoint(event.pos):
                        clicked_profile = profile
                        break

                if clicked_profile:
                    for profile in profiles:
                        # Dispose of old screen surfaces.
                        profile.screen = None
                    active_profile = clicked_profile
                    active_profile.initialise_components()
                    dropdown_open = False

        pygame.display.set_caption(f"Object Viewer: {active_profile.dropdown_label} | {active_profile.object_label(active_profile.get_active_index())}")

    active_profile.screen.fill((30, 30, 30))

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
    cursor_rect = pygame.Rect(
        cursor_x, cursor_y, active_profile.object_scaled_size().w, active_profile.object_scaled_size().h
    )
    pygame.draw.rect(active_profile.screen, (255, 0, 0), cursor_rect, width=3)

    text_surf = font.render(
        f"Key: {active_profile.object_label(active_profile.get_active_index())}", 
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