# file: viewer.py
import pygame
from overworld import load_britannia
from underworld import load_underworld
from tileset import TILE_SIZE

# === CONFIG ===
VIEW_W, VIEW_H = 20, 15   # viewport size in tiles
FPS = 60

def main() -> None:
    pygame.init()
    clock = pygame.time.Clock()

    # Load both maps
    maps = {
        "britannia": load_britannia(),
        "underworld": load_underworld()
    }
    current_map = "britannia"

    # Camera position in tiles
    cam_x, cam_y = 46, 62

    screen = pygame.display.set_mode((VIEW_W * TILE_SIZE, VIEW_H * TILE_SIZE))
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
                    cam_x = max(0, cam_x - 1)
                elif event.key == pygame.K_RIGHT:
                    cam_x = min(maps[current_map].width - VIEW_W, cam_x + 1)
                elif event.key == pygame.K_UP:
                    cam_y = max(0, cam_y - 1)
                elif event.key == pygame.K_DOWN:
                    cam_y = min(maps[current_map].height - VIEW_H, cam_y + 1)

        # Render current viewport
        surf = maps[current_map].render(
            TILE_SIZE,
            rect=(cam_x, cam_y, VIEW_W, VIEW_H)
        )
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()