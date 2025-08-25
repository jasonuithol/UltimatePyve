import pygame
from typing import List
from tileset import load_tiles16, TILE_SIZE

DEFAULT_FRAME_TIME = 0.5

class Sprite:
    def __init__(self, frames: List[pygame.Surface], frame_time: float = DEFAULT_FRAME_TIME):
        self.frames = frames
        self.frame_time = frame_time
        self.current_frame = 0
        self.time_accum = 0.0
        self.world_x = 0
        self.world_y = 0

    @classmethod
    def from_spritesheet(cls, path: str, frame_width: int, frame_height: int,
                         frame_time: float = DEFAULT_FRAME_TIME):
        sheet = pygame.image.load(path).convert_alpha()
        sheet_width, _ = sheet.get_size()
        frames = []
        for x in range(0, sheet_width, frame_width):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (x, 0, frame_width, frame_height))
            frames.append(frame)
        return cls(frames, frame_time)

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

    def draw(self, surface, x, y):
        surface.blit(self.frames[self.current_frame], (x, y))

    def draw_relative_to_camera(self, surface, cam_x, cam_y, tile_size, render_scale):
        screen_x = (self.world_x - cam_x) * tile_size * render_scale
        screen_y = (self.world_y - cam_y) * tile_size * render_scale
        scaled_frame = pygame.transform.scale(
            self.frames[self.current_frame],
            (TILE_SIZE * render_scale, TILE_SIZE * render_scale)
        )
        surface.blit(scaled_frame, (screen_x, screen_y))

# --- Factory function for the Avatar ---
def create_player(frame_time=DEFAULT_FRAME_TIME):
    PLAYER_FIRST_TILE = 332
    PLAYER_FRAME_COUNT = 4
    tileset = load_tiles16(r".\u5\TILES.16")
    frames = tileset[PLAYER_FIRST_TILE:PLAYER_FIRST_TILE + PLAYER_FRAME_COUNT]
    return Sprite(frames, frame_time)

if __name__ == "__main__":
    pygame.init()
    tileset = load_tiles16(r".\u5\TILES.16")

    index = 256  # start of entity bank
    SCALE = 3    # render scale multiplier

    # Make the window big enough for close button + scaled sprite
    win_w = TILE_SIZE * SCALE * 5
    win_h = TILE_SIZE * SCALE + 30  # extra space for index text
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

        if index >= len(tileset):
            index = 0

        # Scale the sprite
        sprite_img = pygame.transform.scale(
            tileset[index],
            (TILE_SIZE * SCALE, TILE_SIZE * SCALE)
        )

        # Draw background, sprite, and index text
        screen.fill((30, 30, 30))
        screen.blit(sprite_img, (0, 0))
        text_surf = font.render(f"Tile {index}", True, (255, 255, 255))
        screen.blit(text_surf, (5, TILE_SIZE * SCALE + 5))

        pygame.display.flip()

