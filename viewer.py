# file: viewer.py
import pygame

from loaders.overworld import load_britannia
from loaders.underworld import load_underworld

from display_engine import DisplayEngine
from sprite import create_player
from map_transitions import load_entry_triggers, spawn_from_trigger
from terrain import can_traverse

def main() -> None:

    game_engine = DisplayEngine()
    player = create_player()
    player.set_position(56, 72)  # starting tile in world coords

    game_engine.register_player(player)

    '''
    pygame.init()
    pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

    screen = pygame.display.set_mode((VIEW_W * TILE_SIZE * USER_SCALE, VIEW_H * TILE_SIZE * USER_SCALE))
    clock = pygame.time.Clock()
    '''

    # Load both maps
    maps = {
        "britannia": load_britannia(),
        "underworld": load_underworld()
    }
    current_map = "britannia"
    current_map_level = 0

    # Load triggers once
    triggers = load_entry_triggers()

    current_location_map = None
    previous_x, previous_y = 0,0
    map_to_render = maps[current_map] # U5Map instance

    running = True
    while running:
        for event in pygame.event.get():

            '''
                TODO: the inside of this loop needs to:
                        - first generate a game state delta
                        - then evaluate if it's allowed
                        - finally update the game state
            '''

            dx,dy = 0,0
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    # Toggle between maps
                    current_map = "underworld" if current_map == "britannia" else "britannia"
                elif event.key == pygame.K_LEFT:
                    dx = -1
                elif event.key == pygame.K_RIGHT:
                    dx = +1
                elif event.key == pygame.K_UP:
                    dy = -1
                elif event.key == pygame.K_DOWN:
                    dy = +1

            target_x = player.world_x + dx
            target_y = player.world_y + dy

            # Only check triggers in overworld/underworld
            if current_location_map is None:
                for tx, ty, location_index in triggers:
                    if target_x == tx and target_y == ty:

                        # Transition to new location
                        current_location_map, target_x, target_y, current_map_level = spawn_from_trigger(location_index)
                        print(f"Entering location {current_location_map.name} ({location_index}) at level {current_map_level}, triggered at ({target_x}, {target_y})")

                        # Move player to spawn point
                        previous_x, previous_y = player.world_x, player.world_y     
                        player.set_position(target_x, target_y)
                        dx, dy = 0, 0
                        break

            # Exit location if outside bounds
            elif not current_location_map is None:
                if (target_x < 0 or target_x >= 32 or
                    target_y < 0 or target_y >= 32):

                    print(f"Returning to {current_map} at ({previous_x}, {previous_y})")

                    # Return to previous map (i.e. the overworld or underworld)
                    current_location_map = None
                    current_map_level = 0
                    player.set_position(previous_x, previous_y)
                    target_x, target_y = previous_x, previous_y
                    dx, dy = 0, 0

                # did not exit location boundaries

            map_to_render = current_location_map if current_location_map is not None else maps[current_map] # U5Map instance

            # Check if non-transitioning move is allowed by terrain.
            if dx == 0 and dy == 0:
                pass
            else:
                if can_traverse(player.transport_mode, map_to_render.get_tile_id(current_map_level, target_x, target_y)):
                    player.move(dx, dy)
                else:
                    # Handle blocked movement (e.g. by displaying a message)
                    print("Movement blocked by terrain.")

            #       
            # Continue processing more events.
            #

        #
        # all events processed.
        #  
        game_engine.set_active_map(map_to_render, current_map_level)

        # update display
        game_engine.render()

        # animate sprites
        game_engine.update_sprites()

    pygame.quit()

if __name__ == "__main__":
    main()