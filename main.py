# file: main.py
import pygame
import gc

from datetime import datetime

from dark_libraries.service_provider import ServiceProvider
from dark_libraries.dark_math        import Coord, Vector2

from animation.animated_tile_factory import AnimatedTileFactory
from animation.flame_sprite_factory  import FlameSpriteFactory
from animation.avatar_sprite_factory import AvatarSpriteFactory
from animation.sprite                import Sprite

from display.display_engine             import DisplayEngine
from display.interactive_console        import InteractiveConsole
from display.lighting.light_map_baker   import LevelLightMapBaker
from display.lighting.light_map_builder import LightMapBuilder
from display.tileset                    import TileLoader
from display.u5_font                    import U5FontLoader, U5GlyphLoader
from display.view_port                  import ViewPort
from display.main_display               import MainDisplay

from game.player_state            import PlayerState
from game.interactable            import InteractableFactoryRegistry, DoorTypeFactory
from game.modding                 import Modding
from game.terrain.terrain_factory import TerrainFactory
from game.world_clock             import WorldClock
from game.map_content.map_content_registry             import MapContentRegistry

from items.consumable_items     import ConsumableItemTypeLoader
from items.equipable_items      import EquipableItemTypeFactory
from items.party_inventory      import PartyInventory
from items.world_loot_loader    import WorldLootLoader
from items.item_type            import InventoryOffset

from maps.u5map_loader   import U5MapLoader
from maps.u5map_registry import U5MapRegistry

from npc.monster_spawner    import MonsterSpawner
from npc.npc_registry       import NpcRegistry
from npc.npc_sprite_factory import NpcSpriteFactory

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
    main_display: MainDisplay
    interactable_factory_registry: InteractableFactoryRegistry
    u5map_registry: U5MapRegistry
    interactive_console: InteractiveConsole
    map_content_registry: MapContentRegistry
    npc_registry: NpcRegistry
#    saved_game: SavedGame

    #
    # TODO: After init, deregister all of these.  Collect all init into a standalone class that can then fall out of scope and then be GC'ed.
    #       For once-off use classes, upgrade ServiceProvider to inject properties into a class without registering that particular class.
    #
    tile_loader: TileLoader
    avatar_sprite_factory: AvatarSpriteFactory
    animated_tile_factory: AnimatedTileFactory
    flame_sprite_factory: FlameSpriteFactory
    terrain_factory: TerrainFactory
    door_type_factory: DoorTypeFactory
    u5map_loader: U5MapLoader
    u5map_registry: U5MapRegistry
    world_loot_loader: WorldLootLoader
    equipable_item_type_factory: EquipableItemTypeFactory
    consumable_item_type_loader: ConsumableItemTypeLoader
    u5_font_loader: U5FontLoader
    u5_glyph_loader: U5GlyphLoader
    light_map_builder: LightMapBuilder
    level_light_map_baker: LevelLightMapBaker
#    saved_game_loader: SavedGameLoader

    npc_sprite_factory: NpcSpriteFactory
    monster_spawner: MonsterSpawner

    modding: Modding
    world_clock: WorldClock

    def init(self):

        pygame.mixer.init()

        self.tile_loader.load_tiles()
        self.animated_tile_factory.register_sprites()
        self.flame_sprite_factory.register_sprites()
        self.terrain_factory.register_terrains()
        self.u5map_loader.register_maps()

        self.u5_font_loader.register_fonts()
        self.u5_glyph_loader.register_glyphs()
        self.npc_sprite_factory.register_npc_sprites()

#        self.saved_game_loader.load_existing()

        self.player_state.set_outer_position(
            u5Map = self.u5map_registry.get_map(0), # britannia/underworld
            level_index = 0,                        # britannia
            coord = Coord(45, 62)                   # starting tile in world coords, just a bit SE of Iolo's Hut.
        )

        self.player_state.set_inner_position(
            u5Map = self.u5map_registry.get_map(13), # Iolo's hut
            level_index = 0,                         
            coord = Coord(15, 15)                    # Inside the hut, OG starting position.
        )

        self.player_state.set_transport_state(
            transport_mode = 0,  # walk
            last_east_west = 0,  # east
            last_nesw_dir = 1    # east
        )

        #
        # TODO: Remove
        #
        self.world_clock.set_world_time(datetime(year=139, month=4, day=5, hour=23, minute=35))

        current_transport_mode, current_direction = self.player_state.get_current_transport_info()

        player_sprite: Sprite = self.avatar_sprite_factory.create_player(
            transport_mode = current_transport_mode, 
            direction      = current_direction
        )
        self.display_engine.set_avatar_sprite(player_sprite)
        self.main_display.init()
        self.display_engine.init()

        # NOTE: this will include chests, orientable furniture, maybe movable furniture ?
        #       one day maybe even the avatar's transports could be these ?
        self.door_type_factory.register_interactable_factories()
        self.equipable_item_type_factory.build()
        self.consumable_item_type_loader.register_item_types()
        self.world_loot_loader.register_loot_containers()

        for u5map in self.u5map_registry.u5maps.values():
            # Requires maps, tiles, sprites, terrain, interactables all loaded first.
            self.map_content_registry.add_u5map(u5map)

        self.light_map_builder.build_light_maps()
        self.level_light_map_baker.bake_level_light_maps()

        #
        # MODS ARE LOADED HERE
        #
        self.modding.load_mods()

        current_u5map, current_level_index, _ = self.player_state.get_current_position()
        
        print("TIM BROOKE-TAYLOR")
        self.player_state._on_changing_map(
            location_index = current_u5map.location_metadata.location_index, 
            level_index    = current_level_index
        )
        self.player_state._on_coord_change()


        #
        # TODO: Need something way better than this
        #

        self.party_inventory.add(InventoryOffset.GOLD,   150)
        self.party_inventory.add(InventoryOffset.FOOD,    63)
        self.party_inventory.add(InventoryOffset.KEYS,    20)
        self.party_inventory.add(InventoryOffset.TORCHES, 40)

        self.interactive_console.print_ascii([i for i in range(128)])
        self.interactive_console.print_rune( [i for i in range(128)])

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
            
        if event.key == pygame.K_i:
            player_state.ignite_torch()
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
                    #
                    # TODO: Create a registry for this
                    #
                    self.world_clock.pass_time()
                    self.interactable_factory_registry.pass_time()
                    self.player_state.pass_time()
                    self.monster_spawner.pass_time()
                    self.npc_registry.pass_time()

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
    # finished initialising, tidy up.
    gc.collect()
    main.run()
