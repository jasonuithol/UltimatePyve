# file: viewer.py
from typing import Tuple, Optional
import pygame

from overworld import load_britannia
from u5map import U5Map
from underworld import load_underworld
from tileset import ega_palette, TILE_SIZE
from sprite import create_player
from map_transitions import load_entry_triggers, spawn_from_trigger
from terrain import can_traverse

# === CONFIG ===
VIEW_W, VIEW_H = 21, 15   # viewport size in tiles
FPS = 60
USER_SCALE = 2  # 1 = native, 2 = double size, etc.

player = create_player()
player.set_position(56, 72)  # starting tile in world coords

def pixels_to_surface(tile_pixels, palette):
    """Convert a 2D list of palette indices into a Pygame Surface."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    for y, row in enumerate(tile_pixels):
        for x, idx in enumerate(row):
            surf.set_at((x, y), palette[idx])
    return surf

def render_map_to_surface(u5map: U5Map, level_ix: int = 0, tile_size: int = TILE_SIZE,
                          rect: Optional[Tuple[int, int, int, int]] = None) -> pygame.Surface:
    """
    Render the map or a subsection of it to a Pygame Surface.
    rect: (tile_x, tile_y, tile_w, tile_h) in tile coordinates.
    """
    if rect is None:
        rect = (0, 0, u5map.width, u5map.height)

    tx, ty, tw, th = rect
    surf = pygame.Surface((tw * tile_size, th * tile_size))

    for y in range(th):
        for x in range(tw):
            map_x = tx + x
            map_y = ty + y
            if 0 <= map_x < u5map.width and 0 <= map_y < u5map.height:
                tid = u5map.get_tile_id(level_ix, map_x, map_y)
                if 0 <= tid < len(u5map.tileset):
                    tile_pixels = u5map.tileset[tid]
                    tile_surf = pixels_to_surface(tile_pixels, u5map.palette)
                    surf.blit(tile_surf, (x * tile_size, y * tile_size))
    return surf

def draw_sprite(surface, sprite, palette, tile_size=TILE_SIZE, render_scale=1,
                cam_x=None, cam_y=None):
    """
    Draw a sprite to the surface.
    If cam_x/cam_y are provided, position is relative to camera (world coords).
    Otherwise, position is treated as screen coords.
    """
    # Determine screen position
    if cam_x is not None and cam_y is not None:
        screen_x = (sprite.world_x - cam_x) * tile_size * render_scale
        screen_y = (sprite.world_y - cam_y) * tile_size * render_scale
    else:
        screen_x = sprite.world_x * tile_size * render_scale
        screen_y = sprite.world_y * tile_size * render_scale

    # Convert raw pixels to a Surface
    frame_pixels = sprite.get_current_frame_pixels()
    frame_surface = pixels_to_surface(frame_pixels, palette)

    # Scale if needed
    if render_scale != 1:
        frame_surface = pygame.transform.scale(
            frame_surface,
            (tile_size * render_scale, tile_size * render_scale)
        )

    # Draw
    surface.blit(frame_surface, (screen_x, screen_y))

def main() -> None:
    pygame.init()
    pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

    clock = pygame.time.Clock()

    # Load both maps
    maps = {
        "britannia": load_britannia(),
        "underworld": load_underworld()
    }
    current_map = "britannia"
    current_map_level = 0

    # Load triggers once
    triggers = load_entry_triggers()

    screen = pygame.display.set_mode((VIEW_W * TILE_SIZE * USER_SCALE, VIEW_H * TILE_SIZE * USER_SCALE))

    current_location_map = None
    previous_x, previous_y = 0,0
    map_to_render = maps[current_map] # U5Map instance

    running = True
    while running:
        for event in pygame.event.get():
            dx,dy = 0,0
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    # Toggle between maps
                    current_map = "underworld" if current_map == "britannia" else "britannia"
                elif event.key == pygame.K_LEFT:
                    dx = -1
                elif event.key == pygame.K_RIGHT:
                    dx = +1
                elif event.key == pygame.K_UP:
                    dy = -1
                elif event.key == pygame.K_DOWN:
                    dy = +1

            target_x = player.world_x + dx
            target_y = player.world_y + dy

            # Only check triggers in overworld/underworld
            if current_location_map is None:
                for tx, ty, location_index in triggers:
                    if target_x == tx and target_y == ty:

                        # Transition to new location
                        current_location_map, target_x, target_y, current_map_level = spawn_from_trigger(location_index)
                        print(f"Entering location {current_location_map.name} ({location_index}) at level {current_map_level}, triggered at ({target_x}, {target_y})")

                        # Move player to spawn point
                        previous_x, previous_y = player.world_x, player.world_y     
                        player.set_position(target_x, target_y)
                        dx, dy = 0, 0
                        break

            # Exit location if outside bounds
            elif not current_location_map is None:
                if (target_x < 0 or target_x >= 32 or
                    target_y < 0 or target_y >= 32):

                    print(f"Returning to {current_map} at ({previous_x}, {previous_y})")

                    # Return to previous map (i.e. the overworld or underworld)
                    current_location_map = None
                    current_map_level = 0
                    player.set_position(previous_x, previous_y)
                # did not exit location boundaries

            map_to_render = current_location_map if current_location_map is not None else maps[current_map] # U5Map instance

            # Check if non-transitioning move is allowed by terrain.
            if dx == 0 and dy == 0:
                pass
            else:
                if can_traverse(player.transport_mode, map_to_render.get_tile_id(current_map_level, target_x, target_y)):
                    player.move(dx, dy)
                else:
                    # Handle blocked movement (e.g. by displaying a message)
                    print("Movement blocked by terrain.")

            #       
            # Continue processing more events.
            #

        #
        # all events processed.
        #  

        pygame.display.set_caption(f"{map_to_render.name} [{player.world_x},{player.world_y}]")

        # update the camera - it follows the player
        cam_x = player.world_x - VIEW_W // 2
        cam_y = player.world_y - VIEW_H // 2

        # Render current viewport from raw map data
        surf = render_map_to_surface(
            map_to_render,
            level_ix=current_map_level,
            tile_size=TILE_SIZE,
            rect=(cam_x, cam_y, VIEW_W, VIEW_H)
        )

        # Scale for display
        surf = pygame.transform.scale(
            surf,
            (VIEW_W * TILE_SIZE * USER_SCALE, VIEW_H * TILE_SIZE * USER_SCALE)
        )

        # Blit to screen
        screen.blit(surf, (0, 0))

        # Draw player relative to camera
        draw_sprite(screen, player, ega_palette, TILE_SIZE, USER_SCALE, cam_x, cam_y)

        pygame.display.flip()
        dt_seconds = clock.tick(FPS) / 1000.0  # dt in seconds

        # Update all animated sprites here
        player.update(dt_seconds)

    pygame.quit()

if __name__ == "__main__":
    main()