# file: main.py
import pygame

from dark_libraries.service_provider import ServiceProvider
from dark_libraries.dark_math import Coord, Vector2

from animation import AnimatedTileFactory, FlameSpriteFactory, AvatarSpriteFactory, Sprite

from display import DisplayEngine

from game.interactable import Action, InteractableFactoryRegistry, DoorTypeFactory
from game import PlayerState
from game.terrain import TerrainFactory

from items.equipable_items import EquipableItemTypeFactory
from items.world_loot_loader import WorldLootLoader
from maps.u5map_loader import U5MapLoader
from maps.u5map_registry import U5MapRegistry
import service_composition

def process_event(player_state: PlayerState, event: pygame.event.Event) -> Action:
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
    return None

class Main:

    # Injectable
    player_state: PlayerState
    display_engine: DisplayEngine
    interactable_factory_registry: InteractableFactoryRegistry
    u5map_registry: U5MapRegistry

    avatar_sprite_factory: AvatarSpriteFactory
    animated_tile_factory: AnimatedTileFactory
    flame_sprite_factory: FlameSpriteFactory
    terrain_factory: TerrainFactory
    door_type_factory: DoorTypeFactory
    u5map_loader: U5MapLoader
    world_loot_loader: WorldLootLoader
    equipable_item_type_factory: EquipableItemTypeFactory

    def init(self):

        self.animated_tile_factory.register_sprites()
        self.flame_sprite_factory.register_sprites()
        self.terrain_factory.register_terrains()
        self.u5map_loader.register_maps()

        self.player_state.set_outer_position(
            u5Map = self.u5map_registry.get_map(0), # britannia/underworld
            level_index = 0,                        # britannia
            coord = Coord(56, 72)                   # starting tile in world coords, just a bit SE of Iolo's Hut.
        )

        self.player_state.set_transport_state(
            transport_mode = 0,  # walk
            last_east_west = 0,  # east
            last_nesw_dir = 1    # east
        )

        player_sprite: Sprite = self.avatar_sprite_factory.create_player(transport_mode=0, direction=0)
        self.display_engine.set_avatar_sprite(player_sprite)

        # NOTE: this will include chests, orientable furniture, maybe movable furniture ?
        #       one day maybe even the avatar's transports could be these ?
        self.door_type_factory.register_interactable_factories()
        self.equipable_item_type_factory.build()
        self.world_loot_loader.register_loot_containers()
        
        self.interactable_factory_registry.load_level(0,0)

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
                        result_action = process_event(self.player_state, event)
                        if result_action is None:
                            print("wtf ?")
                        else:
                            # Allow "in=game" time to pass
                            self.interactable_factory_registry.pass_time()

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
