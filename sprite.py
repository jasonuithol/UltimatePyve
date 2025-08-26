from typing import List
from tileset import load_tiles16_raw, TILE_SIZE, TILES16_PATH

DEFAULT_FRAME_TIME = 0.5

class Sprite:
    def __init__(self, frames: List[List[List[int]]], frame_time: float = DEFAULT_FRAME_TIME):
        """
        frames: list of raw tile pixel arrays (palette indices), not Surfaces
        """
        self.frames = frames
        self.frame_time = frame_time
        self.current_frame = 0
        self.time_accum = 0.0
        self.world_x = 0
        self.world_y = 0

    def set_position(self, tile_x: int, tile_y: int):
        self.world_x = tile_x
        self.world_y = tile_y

    def move(self, dx: int, dy: int):
        self.world_x += dx
        self.world_y += dy

    def update(self, dt: float):
        self.time_accum += dt
        while self.time_accum >= self.frame_time:
            self.time_accum -= self.frame_time
            self.current_frame = (self.current_frame + 1) % len(self.frames)

    def get_current_frame_pixels(self) -> List[List[int]]:
        """Return the raw pixel array for the current frame."""
        return self.frames[self.current_frame]


# --- Factory function for the Avatar ---
def create_player(frame_time=DEFAULT_FRAME_TIME):
    PLAYER_FIRST_TILE = 332
    PLAYER_FRAME_COUNT = 4
    tileset_raw = load_tiles16_raw(TILES16_PATH)
    frames = tileset_raw[PLAYER_FIRST_TILE:PLAYER_FIRST_TILE + PLAYER_FRAME_COUNT]
    return Sprite(frames, frame_time)


if __name__ == "__main__":
    import pygame
    from tileset import ega_palette

    def pixels_to_surface(tile_pixels, palette):
        """Convert a 2D list of palette indices into a Pygame Surface."""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        for y, row in enumerate(tile_pixels):
            for x, idx in enumerate(row):
                surf.set_at((x, y), palette[idx])
        return surf

    pygame.init()
    tileset_raw = load_tiles16_raw(TILES16_PATH)

    index = 256  # start of entity bank
    SCALE = 3

    win_w = TILE_SIZE * SCALE * 5
    win_h = TILE_SIZE * SCALE + 30
    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption("U5 Sprite Viewer")

    font = pygame.font.SysFont(None, 20)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RIGHT:
                    index += 1
                elif event.key == pygame.K_LEFT:
                    index = max(0, index - 1)

        if index >= len(tileset_raw):
            index = 0

        # Convert raw pixels to Surface, then scale
        raw_tile = tileset_raw[index]
        surf_tile = pixels_to_surface(raw_tile, ega_palette)
        sprite_img = pygame.transform.scale(
            surf_tile,
            (TILE_SIZE * SCALE, TILE_SIZE * SCALE)
        )

        screen.fill((30, 30, 30))
        screen.blit(sprite_img, (0, 0))
        text_surf = font.render(f"Tile {index}", True, (255, 255, 255))
        screen.blit(text_surf, (5, TILE_SIZE * SCALE + 5))

        pygame.display.flip()