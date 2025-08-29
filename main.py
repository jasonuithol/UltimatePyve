# file: viewer.py
import pygame

from sprite import Sprite, create_player
from display_engine import DisplayEngine
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

    display_engine = DisplayEngine()

    player_state = PlayerState(
        outer_map=load_britannia(), 
        outer_coord=Coord(56, 72)    # starting tile in world coords, just a bit SE of Iolo's Hut.
    )

    player_sprite: Sprite = create_player(transport_mode=0, direction=0)
    player_sprite.set_position(player_state.outer_coord)  

    display_engine.register_sprite(player_sprite)

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
        display_engine.set_active_map(new_map, new_level)

        transport_mode, direction = player_state.get_current_transport_info()
        # this will reset animations constantly - so sprites need to be stateless HAHAHAHAHAHAH
        display_engine.unregister_sprite(player_sprite)
        player_sprite = create_player(transport_mode, direction)
        display_engine.register_sprite(player_sprite)

        # for the player - this feels pointless.  but other sprites will appreciate the effort.
        player_sprite.set_position(new_coords)

        # update display
        display_engine.render(new_coords)

    pygame.quit()

if __name__ == "__main__":
    main()