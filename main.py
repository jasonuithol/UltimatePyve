# file: main.py
import pygame
from animation.animated_tile_factory import AnimatedTileFactory
from animation.flame_sprite_factory import FlameSpriteFactory
from dark_libraries.service_provider import ServiceProvider
from dark_libraries.dark_math import Coord, Vector2

from animation.sprite import Sprite
from animation.avatar_sprite_factory import AvatarSpriteFactory
from display.display_engine import DisplayEngine
import game.door_type_factory as door_type_factory
from game.interactable import InteractionResult
from game.player_state import PlayerState
from game.terrain_factory import TerrainFactory
from loaders.overworld import Britannia
from loaders.tileset import TileSet

import service_composition

def process_event(player_state: PlayerState, event: pygame.event.Event) -> InteractionResult:
    if event.key == pygame.K_TAB:
        return player_state.switch_outer_map()
    elif event.key == pygame.K_BACKQUOTE:
        return player_state.rotate_transport()
    elif event.key == pygame.K_LEFT:
        return player_state.move(Vector2(-1, 0))
    elif event.key == pygame.K_RIGHT:
        return player_state.move(Vector2(+1, 0))
    elif event.key == pygame.K_UP:
        return player_state.move(Vector2(0, -1))
    elif event.key == pygame.K_DOWN:
        return player_state.move(Vector2(0, +1))
    
    # Nothing changed
    return InteractionResult.error("wtf ?")

class Main:

    # Injectable
    tileset: TileSet
    player_state: PlayerState
    display_engine: DisplayEngine

    avatar_sprite_factory: AvatarSpriteFactory
    animated_tile_factory: AnimatedTileFactory
    flame_sprite_factory: FlameSpriteFactory
    terrain_factory: TerrainFactory
    door_type_factory: door_type_factory.DoorTypeFactory

    def init(self):

        self.player_state.set_outer_position(
            u5Map = provider.resolve(Britannia),
            coord = Coord(56, 72) # starting tile in world coords, just a bit SE of Iolo's Hut.
        )

        self.player_state.set_transport_state(
            transport_mode = 0,  # walk
            last_east_west = 0,  # east
            last_nesw_dir = 1    # east
        )

        player_sprite: Sprite = self.avatar_sprite_factory.create_player(transport_mode=0, direction=0)
        self.display_engine.set_avatar_sprite(player_sprite)

        self.animated_tile_factory.register_sprites()
        self.flame_sprite_factory.register_sprites()
        self.terrain_factory.register_terrains()

        # NOTE: this will include chests, orientable furniture, maybe movable furniture ?
        #       one day maybe even the avatar's transports could be these ?
        self.door_type_factory.register_interactable_factories()

    def run(self) -> None:

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        interaction_result = process_event(self.player_state, event)
                        if interaction_result is None:
                            print("wtf ?")
                        else:
                            if interaction_result.message and len(interaction_result.message):
                                if interaction_result.success == False:
                                    print(f"{interaction_result.message} :(")
                                else:
                                    print(f"{interaction_result.message} :)")

            #
            # all events processed.
            #  
            new_map, new_level, new_coords = self.player_state.get_current_position()
            self.display_engine.set_active_map(new_map, new_level)

            # Player sprite
            transport_mode, direction = self.player_state.get_current_transport_info()
            player_sprite = self.avatar_sprite_factory.create_player(transport_mode, direction)
            self.display_engine.set_avatar_sprite(player_sprite)

            # update display
            self.display_engine.render(new_coords)

        pygame.quit()

if __name__ == "__main__":

    provider = ServiceProvider()
    service_composition.compose(provider)

    print("Pre-registering Main")
    provider.register(Main)

    provider.inject_all()

    main: Main = provider.resolve(Main)
    main.init()
    main.run()
