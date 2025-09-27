# file: main.py
import pygame

from dark_libraries.service_provider import ServiceProvider
from dark_libraries.dark_math import Coord, Vector2

from animation import AnimatedTileFactory, FlameSpriteFactory, AvatarSpriteFactory, Sprite

from display import DisplayEngine

from display.interactive_console import InteractiveConsole
from display.view_port import ViewPort
from game import PlayerState #, SavedGame, SavedGameLoader
from game.interactable import InteractableFactoryRegistry, DoorTypeFactory
from game.modding import Modding
from game.terrain import TerrainFactory

from game.world_clock import WorldClock
from items import ConsumableItemTypeLoader, EquipableItemTypeFactory, PartyInventory, WorldLootLoader

from items.item_type import InventoryOffset
from maps import U5MapLoader, U5MapRegistry

import service_composition

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
    view_port: ViewPort
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

    modding: Modding
    world_clock: WorldClock

    def init(self):

        pygame.mixer.init()

        self.animated_tile_factory.register_sprites()
        self.flame_sprite_factory.register_sprites()
        self.terrain_factory.register_terrains()
        self.u5map_loader.register_maps()
#        self.saved_game_loader.load_existing()

        self.player_state.set_outer_position(
            u5Map = self.u5map_registry.get_map(0), # britannia/underworld
            level_index = 0,                        # britannia
            coord = Coord(45, 62)                   # starting tile in world coords, just a bit SE of Iolo's Hut.
        )

        self.player_state.set_inner_position(
            u5Map = self.u5map_registry.get_map(13), # Iolo's hut
            level_index = 0,                         
            coord = Coord(24, 3)                     # just south of the potion barrel, in the stables.
        )

        self.player_state.set_transport_state(
            transport_mode = 0,  # walk
            last_east_west = 0,  # east
            last_nesw_dir = 1    # east
        )

        current_transport_mode, current_direction = self.player_state.get_current_transport_info()

        player_sprite: Sprite = self.avatar_sprite_factory.create_player(
            transport_mode = current_transport_mode, 
            direction      = current_direction
        )
        self.display_engine.set_avatar_sprite(player_sprite)
        self.view_port.init()

        # NOTE: this will include chests, orientable furniture, maybe movable furniture ?
        #       one day maybe even the avatar's transports could be these ?
        self.door_type_factory.register_interactable_factories()
        self.equipable_item_type_factory.build()
        self.consumable_item_type_loader.register_item_types()
        self.world_loot_loader.register_loot_containers()
        
        #
        # MODS ARE LOADED HERE
        #
        self.modding.load_mods()

        current_u5map, current_level_index, _ = self.player_state.get_current_position()
        
        self.player_state._on_changing_map(
            location_index = current_u5map.location_metadata.location_index, 
            level_index    = current_level_index
        )

        #
        # TODO: Need something way better than this
        #

        self.party_inventory.add(InventoryOffset.GOLD,   150)
        self.party_inventory.add(InventoryOffset.FOOD,    63)
        self.party_inventory.add(InventoryOffset.KEYS,     2)
        self.party_inventory.add(InventoryOffset.TORCHES,  4)

        self.interactive_console.print_ascii([i for i in range(128)])
        self.interactive_console.print_rune([i for i in range(128)])

        # Sun and moon phases
        self.interactive_console.print_rune([42,48,49,50,51,52,53,54,55])

    def update(self):
        new_map, new_level, new_coords = self.player_state.get_current_position()
        self.display_engine.set_active_map(new_map, new_level)

        # Player sprite
        transport_mode, direction = self.player_state.get_current_transport_info()
        player_sprite = self.avatar_sprite_factory.create_player(transport_mode, direction)
        self.display_engine.set_avatar_sprite(player_sprite)

        # update display
        self.display_engine.render(new_coords)

    def obtain_action_direction(self) -> Vector2:

        self.interactive_console.print_ascii("Direction ?")

        in_loop = True
        while in_loop:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    in_loop = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        in_loop = False
                    else:
                        direction = get_direction(event)
                        if not direction is None:
                            return direction

            #
            # all events processed.
            #  
            self.update()

        return None
    
    def process_event(self, player_state: PlayerState, event: pygame.event.Event):

        if event.key == pygame.K_TAB:
            player_state.switch_outer_map()
            return

        if event.key == pygame.K_BACKQUOTE:
            player_state.rotate_transport()
            return
         
        move_direction = get_direction(event)
        if not move_direction is None:
            player_state.move(move_direction)
            return 

        if event.key == pygame.K_j:
            direction = self.obtain_action_direction()
            if direction:
                player_state.jimmy(direction)
                return
        # Nothing changed
    
    def run(self):

        running = True
        while running:
            for event in pygame.event.get():

                # Should only process KEYDOWN events as being "actions" that pass time.
                player_input_received = False

                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        player_input_received = True
                        self.process_event(self.player_state, event)

                # Allow "in=game" time to pass
                if player_input_received:
                    self.interactable_factory_registry.pass_time()
                    self.world_clock.pass_time()

                    # TODO: Remove
                    self.interactive_console.print_rune(self.world_clock.get_celestial_panorama())

            #
            # all events processed.
            #  
            self.update()

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
