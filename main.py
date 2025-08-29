# file: viewer.py
import pygame

from display_engine import DisplayEngine
from sprite import create_player
from player_state import PlayerState
from dark_math import Coord, Vector2

from loaders.overworld import load_britannia

def process_event(player_state: PlayerState, event: pygame.event.Event) ->PlayerState:
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
    return player_state

def main() -> None:

    game_engine = DisplayEngine()

    player_state = PlayerState(
        outer_map=load_britannia(), 
        outer_coord=Coord(56, 72)    # starting tile in world coords, just a bit SE of Iolo's Hut.
    )

    player_sprite = create_player()
    player_sprite.set_position(player_state.outer_coord)  

    game_engine.register_player(player_sprite)

    running = True
    while running:
        for event in pygame.event.get():
            new_state: PlayerState = None
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    new_state = process_event(player_state, event)
                    if new_state is None:
                        print("Action was forbidden !")
                    else:
                        player_state = new_state

        #
        # all events processed.
        #  
        new_map, new_level, new_coords = player_state.get_current_position()

        game_engine.set_active_map(new_map, new_level)
        player_sprite.set_position(new_coords)

        # update display
        game_engine.render()

        # animate sprites
        game_engine.update_sprites()

    pygame.quit()

if __name__ == "__main__":
    main()