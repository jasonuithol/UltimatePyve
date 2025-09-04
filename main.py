# file: main.py
import pygame
from dark_libraries.service_provider import ServiceProvider
import game.doors as doors

from game.interactable import InteractionResult
from animation.sprite import Sprite, AvatarSpriteFactory
from display.display_engine import DisplayEngine
from game.player_state import PlayerState
from dark_libraries.dark_math import Coord, Vector2

from loaders import service_composition
from loaders.location import LocationLoader
from loaders.overworld import Britannia #, load_britannia
from loaders.tileset import TileSet #, load_tileset
from game.world_state import WorldState

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

def main() -> None:

    provider = ServiceProvider(allow_auto=True)
    service_composition.compose(provider)

    tileset: TileSet = provider.get(TileSet)
#    world_state = WorldState()
    world_state: WorldState = provider.get(WorldState)

    for tile_id, door_factory in doors.build_all_door_types().items():
        world_state.register_interactable_factory(tile_id, door_factory)

#    display_engine = DisplayEngine(world_state=world_state, tileset=tileset)
    display_engine: DisplayEngine = provider.get(DisplayEngine)

    player_state = PlayerState(
        world_state=world_state,
        location_loader=provider.get(LocationLoader),
#        outer_map=load_britannia(), 
        outer_map=provider.get(Britannia),
        outer_coord=Coord(56, 72)    # starting tile in world coords, just a bit SE of Iolo's Hut.
    )

#    avatar_sprite_factory = AvatarSpriteFactory(tileset=tileset)
    avatar_sprite_factory: AvatarSpriteFactory = provider.get(AvatarSpriteFactory)

    player_sprite: Sprite = avatar_sprite_factory.create_player(transport_mode=0, direction=0)
    player_sprite.set_position(player_state.outer_coord)  

    display_engine.register_sprite(player_sprite)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    interaction_result = process_event(player_state, event)
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
        new_map, new_level, new_coords = player_state.get_current_position()
        display_engine.set_active_map(new_map, new_level)

        # this will reset animations constantly - so sprites need to be stateless HAHAHAHAHAHAH
        display_engine.clear_sprites()

        # Player sprite
        transport_mode, direction = player_state.get_current_transport_info()
        player_sprite = avatar_sprite_factory.create_player(transport_mode, direction)
        player_sprite.set_position(new_coords)
        display_engine.register_sprite(player_sprite)

        # update display
        display_engine.render(new_coords)

    pygame.quit()

if __name__ == "__main__":
    main()