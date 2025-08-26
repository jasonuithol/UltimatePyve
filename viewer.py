# file: viewer.py
import pygame
from overworld import load_britannia
from underworld import load_underworld
from tileset import TILE_SIZE
from sprite import create_player

# === CONFIG ===
VIEW_W, VIEW_H = 21, 15   # viewport size in tiles
FPS = 60
USER_SCALE = 2  # 1 = native, 2 = double size, etc.

player = create_player()
player.set_position(56, 72)  # starting tile in world coords


def main() -> None:
    pygame.init()
    clock = pygame.time.Clock()

    # Load both maps
    maps = {
        "britannia": load_britannia(),
        "underworld": load_underworld()
    }
    current_map = "britannia"
    current_map_level = 0

    # Camera position in tiles
    cam_x, cam_y = 46, 62

    screen = pygame.display.set_mode((VIEW_W * TILE_SIZE * USER_SCALE, VIEW_H * TILE_SIZE * USER_SCALE))
    pygame.display.set_caption("Ultima V Map Viewer")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    # Toggle between maps
                    current_map = "underworld" if current_map == "britannia" else "britannia"
                elif event.key == pygame.K_LEFT:
                    player.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    player.move(1, 0)
                elif event.key == pygame.K_UP:
                    player.move(0, -1)
                elif event.key == pygame.K_DOWN:
                    player.move(0, 1)

        # update the camera - it follows the player
        cam_x = player.world_x - VIEW_W // 2
        cam_y = player.world_y - VIEW_H // 2

        # Render current viewport
        surf = maps[current_map].render(current_map_level, TILE_SIZE, rect=(cam_x, cam_y, VIEW_W, VIEW_H))
        surf = pygame.transform.scale(
            surf, (VIEW_W * TILE_SIZE * USER_SCALE, VIEW_H * TILE_SIZE * USER_SCALE)
        )
        screen.blit(surf, (0, 0))

        # Draw player relative to camera
        player.draw_relative_to_camera(screen, cam_x, cam_y, TILE_SIZE, USER_SCALE)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()