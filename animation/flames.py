# file: animation/flames.py
from typing import Optional, Dict, Iterator
from animation.sprite import Sprite
from loaders.tileset import Tile
import pygame

import random

'''
TILE.16 contains 8 flame overlay tiles for animating specific "normal" tiles that have flames

192 & 193 are for left and right torches [176,177] (that's why they look so similar) 
194 is for standing braziers [178] and almost definitely flames of truth/love/courage [222] 
195 is definitely for campfire [179] 
204 is for the fireplace [188]
205 is for the lamppost [189]
206 is for the 3 pronged candelabra that sits on tables [190]
207 is for the stove/over, it looks a bit blobular but it just happens to fit inside the rentangular opening that the stove/oven has [191]

with the exception of the flames of truth etc - there's a simple formula that maps "normal" tile to it's flame overlay

FLAME_OVERLAY_INDEX = NORMAL_TILE_INDEX + 16
'''

_sprite_cache: Dict[int, Sprite] = {}

_flame_animatable = [
    176,177,178,222,179,188,189,190,191
]

def has_flame_animation(tile_index: int):
    return tile_index in _flame_animatable

def get_flame_overlay_index(tile_index: int) -> Optional[int]:
    if not has_flame_animation(tile_index):
        return None
    
    if tile_index == 222:
        return get_flame_overlay_index(178)
    
    return tile_index + 16

def _build_frames(original_tile_id: int) -> Iterator[Tile]:
    assert has_flame_animation(original_tile_id), f"Tile id={original_tile_id} is not flame-animatable."

    from loaders.tileset import load_tileset
    tileset = load_tileset()

    original_tile: Tile = tileset.tiles[original_tile_id]
    overlay_tile: Tile = tileset.tiles[get_flame_overlay_index(original_tile_id)]

    cycle_length = 23       # arbitrary prime number

    # Apply overlay mask
    for _ in range(cycle_length):
        composed_surface = original_tile.to_surface().copy()
        for y, row in enumerate(overlay_tile.pixels):
            for x, mask_val in enumerate(row):
                composed_value = original_tile.pixels[y][x]
                for bit_ix in range(8):
                    bit_selector = 1 << bit_ix
                    if bit_selector & mask_val:
                        # RANDOMLY TOGGLE ORIGINAL
                        if random.choice([True, False]):
                            composed_value ^= bit_selector
                    else:
                        # leave original alone
                        pass

                composed_surface.set_at((x, y), tileset.palette[composed_value])

        composed_tile = Tile(None)
        composed_tile.set_surface(composed_surface)
        yield composed_tile

'''
def _build_frames_test(original_tile_id: int) -> Iterator[Tile]:
    from loaders.tileset import Tile, TILE_SIZE
    import pygame

    # Ten distinct colours — easy to spot if animation is working
    colors = [
        (255,   0,   0),  # red
        (  0, 255,   0),  # green
        (  0,   0, 255),  # blue
        (255, 255,   0),  # yellow
        (255,   0, 255),  # magenta
        (  0, 255, 255),  # cyan
        (255, 128,   0),  # orange
        (128,   0, 255),  # purple
        (  0, 128, 255),  # sky blue
        (128, 128, 128),  # grey
    ]

    for color in colors:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(color)
        tile = Tile(None)
        tile.set_surface(surf)
        yield tile
'''
def build_sprite(tile_id: int) -> Sprite:
    FRAME_TIME = 0.15
    global _sprite_cache
    if not tile_id in _sprite_cache.keys():
        frames = list(_build_frames(tile_id))
        _sprite_cache[tile_id] = Sprite(
            frames=frames,
            frame_time=FRAME_TIME
        )
    return _sprite_cache[tile_id]

def build_all_sprites() -> Dict[int, Sprite]:
    for tile_id in _flame_animatable:
        build_sprite(tile_id)
    return _sprite_cache

#
# MAIN
#
if __name__ == "__main__":

    from loaders.tileset import load_tileset
    tileset = load_tileset()

    selection_index = 0
    current_tile_id = _flame_animatable[selection_index]
    current_sprite = build_sprite(current_tile_id)
    index_delta = 0
    frame_time = 0.2

    # onto the magic stuff

    import pygame

    pygame.init()
    pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

    SCALE = 20
    FPS = 60

    screen = pygame.display.set_mode((tileset.tile_size * SCALE, tileset.tile_size * SCALE))
    clock = pygame.time.Clock()

    running = True

    while running:
        for event in pygame.event.get():
            index_delta = 0
            frame_time_delta = 0

            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RIGHT:
                    index_delta = -1
                elif event.key == pygame.K_LEFT:
                    index_delta = +1
                elif event.key == pygame.K_UP:
                    frame_time_delta = +1
                elif event.key == pygame.K_DOWN:
                    frame_time_delta = -1

            if index_delta != 0:
                selection_index = (selection_index + index_delta) % len(_flame_animatable)
                current_tile_id = _flame_animatable[selection_index]
                current_sprite = build_sprite(current_tile_id)

            frame_time += (frame_time_delta * 0.01)
            if frame_time < 0.01:
                frame_time = 0.01

        current_sprite.set_frame_time(frame_time, 0.0)
        current_frame = current_sprite.get_current_frame_tile(pygame.time.get_ticks())

        scaled = pygame.transform.scale(current_frame.surface, (tileset.tile_size * SCALE, tileset.tile_size * SCALE))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()

