import pygame
import sys
import os
import struct
import random

# --- CONFIG ---
DATA_DIR = r"C:\Program Files (x86)\GOG Galaxy\Games\Ultima 5"   # Change to your Ultima V folder
MAP_FILE = os.path.join(DATA_DIR, "BRIT.DAT")
TILE_SIZE = 16
SCALE = 1  # integer scaling for display

CHUNK_DIM = 16      # tiles per chunk side
CHUNKS_X = 32
CHUNKS_Y = 32
MAP_WIDTH = CHUNK_DIM * CHUNKS_X
MAP_HEIGHT = CHUNK_DIM * CHUNKS_Y

# --- LOAD MAP ---
def load_brit_dat(path):
    with open(path, "rb") as f:
        # Read chunk index table (32x32 entries, each 2 bytes, little-endian)
        index_table = []
        for _ in range(CHUNKS_X * CHUNKS_Y):
            offset_bytes = f.read(2)
            if len(offset_bytes) < 2:
                raise ValueError("Unexpected end of file in index table")
            offset = struct.unpack("<H", offset_bytes)[0]
            index_table.append(offset)

        # Now read each chunk
        chunks = []
        for idx, offset in enumerate(index_table):
            f.seek(offset)
            chunk_data = f.read(CHUNK_DIM * CHUNK_DIM)
            if len(chunk_data) < CHUNK_DIM * CHUNK_DIM:
                raise ValueError(f"Chunk {idx} truncated")
            # Convert to 2D list
            chunk_tiles = [
                list(chunk_data[y*CHUNK_DIM:(y+1)*CHUNK_DIM])
                for y in range(CHUNK_DIM)
            ]
            chunks.append(chunk_tiles)

    # Assemble full map
    full_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    for cy in range(CHUNKS_Y):
        for cx in range(CHUNKS_X):
            chunk_index = cy * CHUNKS_X + cx
            chunk = chunks[chunk_index]
            for ty in range(CHUNK_DIM):
                for tx in range(CHUNK_DIM):
                    full_map[cy*CHUNK_DIM + ty][cx*CHUNK_DIM + tx] = chunk[ty][tx]
    return full_map

# --- FAKE TILESET ---
def generate_fake_tiles():
    tileset = {}
    for tid in range(256):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill((random.randint(50, 200),
                   random.randint(50, 200),
                   random.randint(50, 200)))
        tileset[tid] = surf
    return tileset

# --- MAIN ---
def main():
    pygame.init()
    tiles = load_brit_dat(MAP_FILE)
    tileset = generate_fake_tiles()

    screen = pygame.display.set_mode(
        (MAP_WIDTH * TILE_SIZE * SCALE, MAP_HEIGHT * TILE_SIZE * SCALE)
    )
    pygame.display.set_caption("Ultima V - BRIT.DAT Chunk Viewer")

    # Render map to a single surface
    map_surface = pygame.Surface((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tid = tiles[y][x]
            map_surface.blit(tileset[tid], (x * TILE_SIZE, y * TILE_SIZE))

    # Scale for display
    if SCALE != 1:
        map_surface = pygame.transform.scale(
            map_surface,
            (map_surface.get_width() * SCALE, map_surface.get_height() * SCALE)
        )

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.blit(map_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
