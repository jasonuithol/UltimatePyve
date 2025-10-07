# file: animation/flames.py
import pygame
import random
from typing import Optional, Iterator

from data.global_registry import GlobalRegistry
from view.display_config import DisplayConfig
from models.tile import Tile

from models.sprite import Sprite

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

class FlameSpriteLoader:

    # Injectable
    display_config: DisplayConfig
    global_registry: GlobalRegistry

    def _after_inject(self):

        self._flame_animatable = [
            176,177,178,222,179,188,189,190,191
        ]

    def _has_flame_animation(self, tile_index: int):
        return tile_index in self._flame_animatable

    def _get_flame_overlay_index(self, tile_index: int) -> Optional[int]:
        if not self._has_flame_animation(tile_index):
            return None
        
        if tile_index == 222:
            return self._get_flame_overlay_index(178)
        
        return tile_index + 16

    def _build_frames(self, original_tile_id: int) -> Iterator[Tile]:
        assert self._has_flame_animation(original_tile_id), f"Tile id={original_tile_id} is not flame-animatable."

        original_tile: Tile = self.global_registry.tiles.get(original_tile_id)
        overlay_tile:  Tile = self.global_registry.tiles.get(self._get_flame_overlay_index(original_tile_id))

        cycle_length = 23       # arbitrary prime number

        # Apply overlay mask
        for _ in range(cycle_length):
            composed_surface = original_tile.get_surface().copy()
            for y, row in enumerate(overlay_tile.pixels):
                for x, mask_val in enumerate(row):
                    composed_value = original_tile.pixels[y][x]
                    for bit_ix in range(8):
                        bit_selector = 1 << bit_ix
                        if bit_selector & mask_val:
                            # RANDOMLY TOGGLE ORIGINAL
                            if random.choice([True, False]):
                                composed_value ^= bit_selector   # XOR function - i.e. for every bit in the following values: e.g. 1010
                                                                 #                          if bit_selector is 1, then: 
                                                                 #                              if mask_val is 1, set to 0, and vice-versa
                        else:
                            # leave original alone
                            pass

                    composed_surface.set_at((x, y), self.display_config.EGA_PALETTE[composed_value])

            composed_tile = Tile(None)
            composed_tile.set_surface(composed_surface)
            yield composed_tile

    def _build_sprite(self, tile_id: int) -> Sprite:
        FRAME_TIME = 0.15
        frames = list(self._build_frames(tile_id))

        sprite = Sprite(
            frames=frames,
            frame_time=FRAME_TIME
        )
        return sprite

    def register_sprites(self):
        for tile_id in self._flame_animatable:
            sprite = self._build_sprite(tile_id)
            self.global_registry.sprites.register(tile_id, sprite)

#
# MAIN
#
if __name__ == "__main__":

    from data.loaders.tileset_loader import TileLoader

    display_config = DisplayConfig()
    global_registry = GlobalRegistry()
    global_registry._after_inject()

    tile_factory = TileLoader()
    tile_factory.display_config = display_config
    tile_factory.global_registry = global_registry
    tile_factory.load_tiles()

    loader = FlameSpriteLoader()
    loader.display_config = display_config
    loader.global_registry = global_registry
    loader._after_inject()
    
    loader.register_sprites()

    keys = list(global_registry.sprites.keys())

    selection_index = 0
    current_tile_id = keys[selection_index]
    current_sprite: Sprite = global_registry.sprites.get(current_tile_id)
    index_delta = 0
    frame_time = 0.2

    # onto the magic stuff

    import pygame

    pygame.init()
    pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

    SCALE = 20
    FPS = 60

    screen = pygame.display.set_mode(display_config.TILE_SIZE.scale(SCALE).to_tuple())
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
                selection_index = (selection_index + index_delta) % len(global_registry.sprites)
                current_tile_id = keys[selection_index]
                current_sprite: Sprite = global_registry.sprites.get(current_tile_id)

            frame_time += (frame_time_delta * 0.01)
            if frame_time < 0.01:
                frame_time = 0.01

        current_sprite.set_frame_time(frame_time, 0.0)
        current_frame = current_sprite.get_current_frame_tile(pygame.time.get_ticks())

        scaled = pygame.transform.scale(current_frame.surface, display_config.TILE_SIZE.scale(SCALE).to_tuple())
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()

