# file: main.py
import pygame

from dark_libraries.service_provider import ServiceProvider
from dark_libraries.dark_math import Coord, Vector2

from animation import AnimatedTileFactory, FlameSpriteFactory, AvatarSpriteFactory, Sprite

from display import DisplayEngine

from display.interactive_console import InteractiveConsole
from game import PlayerState #, SavedGame, SavedGameLoader
from game.interactable import Action, InteractableFactoryRegistry, DoorTypeFactory
from game.terrain import TerrainFactory

from items import ConsumableItemTypeLoader, EquipableItemTypeFactory, PartyInventory, WorldLootLoader
from items.consumable_items import TileId as ConsumableTileId

from maps import U5MapLoader, U5MapRegistry

import service_composition

def process_event(player_state: PlayerState, event: pygame.event.Event) -> Action:

    if event.key == pygame.K_TAB:
        return player_state.switch_outer_map()

    if event.key == pygame.K_BACKQUOTE:
        return player_state.rotate_transport()

    move_direction = get_direction(event)
    if not move_direction is None:
        return player_state.move(move_direction)

    if event.key == pygame.K_j:
        return player_state.jimmy()

    # Nothing changed
    return None

def get_direction(event: pygame.event.Event) -> Vector2:
    if event.key == pygame.K_LEFT:
        return Vector2(-1, 0)
    elif event.key == pygame.K_RIGHT:
        return Vector2(+1, 0)
    elif event.key == pygame.K_UP:
        return Vector2(0, -1)
    elif event.key == pygame.K_DOWN:
        return Vector2(0, +1)
    return None

class Main:

    # Injectable
    player_state: PlayerState
    party_inventory: PartyInventory
    display_engine: DisplayEngine
    interactable_factory_registry: InteractableFactoryRegistry
    u5map_registry: U5MapRegistry
    interactive_console: InteractiveConsole
#    saved_game: SavedGame

    avatar_sprite_factory: AvatarSpriteFactory
    animated_tile_factory: AnimatedTileFactory
    flame_sprite_factory: FlameSpriteFactory
    terrain_factory: TerrainFactory
    door_type_factory: DoorTypeFactory
    u5map_loader: U5MapLoader
    world_loot_loader: WorldLootLoader
    equipable_item_type_factory: EquipableItemTypeFactory
    consumable_item_type_loader: ConsumableItemTypeLoader
#    saved_game_loader: SavedGameLoader

    def init(self):

        self.animated_tile_factory.register_sprites()
        self.flame_sprite_factory.register_sprites()
        self.terrain_factory.register_terrains()
        self.u5map_loader.register_maps()
#        self.saved_game_loader.load_existing()

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

        #
        # TODO: Need something way better than this
        #

        self.party_inventory.add(ConsumableTileId.GOLD.value, 150)
        self.party_inventory.add(ConsumableTileId.FOOD.value,  63)
        self.party_inventory.add(ConsumableTileId.KEY.value,    2)
        self.party_inventory.add(ConsumableTileId.TORCH.value,  4)
    

        player_sprite: Sprite = self.avatar_sprite_factory.create_player(transport_mode=0, direction=0)
        self.display_engine.set_avatar_sprite(player_sprite)

        # NOTE: this will include chests, orientable furniture, maybe movable furniture ?
        #       one day maybe even the avatar's transports could be these ?
        self.door_type_factory.register_interactable_factories()
        self.equipable_item_type_factory.build()
        self.consumable_item_type_loader.register_item_types()
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
                            result_action = result_action.to_action()
                            assert isinstance(result_action, Action), f"Did not receive an Action from process_events, got {result_action!r}"
                            if "msg" in result_action.action_parameters:
                                self.interactive_console.print_ascii(result_action.action_parameters["msg"])
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
