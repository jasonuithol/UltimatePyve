# file: game/player_state.py
from datetime import timedelta
from typing import Iterable

from controllers.display_controller import DisplayController
from dark_libraries.dark_math import Coord, Vector2
from dark_libraries.logging   import LoggerMixin
from data.global_registry     import GlobalRegistry

from models.global_location   import GlobalLocation
from models.interactable      import Interactable
from models.move_into_result  import MoveIntoResult
from models.enums.inventory_offset  import InventoryOffset
from models.sprite            import Sprite
from models.terrain           import Terrain
from models.u5_map             import U5Map

# singletons
from models.party_inventory   import PartyInventory
from models.party_state       import PartyState

from services.avatar_sprite_factory import AvatarSpriteFactory
from services.sound_track_player     import SoundTrackPlayer
from services.world_clock     import WorldClock

from services.console_service import ConsoleService

#from .saved_game import SavedGame

class PartyController(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    party_inventory: PartyInventory
    party_state:     PartyState

    console_service:       ConsoleService
    sound_track_player:    SoundTrackPlayer
    world_clock:           WorldClock
    avatar_sprite_factory: AvatarSpriteFactory

    display_controller: DisplayController
    
    # Anything changing map, OR level should call this.
    def _on_change_map_level(self, new_location_index: int, new_level_index: int):
        self.display_controller.set_active_map(new_location_index, new_level_index)

        '''
        self.world_loot_service.register_loot_containers()
        self.map_cache_service.init()
        '''


    def _say_blocked(self):
        self.console_service.print_ascii("Blocked !")

    # good for loading a SAVE.GAM location that's in a town or dungeon or something, and you need to eventually 
    # resolve the overworld position when exiting.
    def load_inner_location(self, inner_location: GlobalLocation):

        # Get outer world coords for starting position
        # will need this trick when importing saved games from OG U5 files.
        outer_location: GlobalLocation = None
        for entry_location, exit_location in self.global_registry.entry_triggers.items():
            if exit_location.location_index == inner_location.location_index:
                outer_location = entry_location
        
        assert not outer_location is None, f"Could not load overworld location for {inner_location}"

        self.party_state.clear_locations()
        self.party_state.push_location(outer_location)
        self.party_state.push_location(inner_location)

        self._on_change_map_level(inner_location.location_index, inner_location.level_index)

        self.log(f"Set party location to outer={outer_location}, inner={inner_location}")

    def load_transport_state(self):
        self.party_state.set_transport_state(
            transport_mode = 0,  # walk
            last_east_west = 0,  # east
            last_nesw_dir = 1    # east
        )

        current_transport_mode, current_direction = self.party_state.get_transport_state()

        player_sprite: Sprite = self.avatar_sprite_factory.create_player(
            transport_mode = current_transport_mode, 
            direction      = current_direction
        )
        self.display_controller.set_avatar_sprite(player_sprite)

        self.log(
            f"Set party transport state to transport_mode={self.party_state.transport_mode}" 
            + 
            f", last_east_west={self.party_state.last_east_west}"
            +
            f", last_nesw_dir={self.party_state.last_nesw_dir}"
        )

    def load_party_inventory(self, inventory: Iterable[tuple[InventoryOffset, int]]):
        for inventory_offset, additional_quantity in inventory:
            self.party_inventory.add(inventory_offset, additional_quantity)

    # TODO: Choose a better name for this method
    def can_traverse(self, target: Coord) -> MoveIntoResult:

        transport_mode     = self.global_registry.transport_modes.get(self.transport_mode)
        current_location   = self.party_state.get_current_location()
        current_map: U5Map = self.global_registry.maps.get(current_location.location_index)
        target_tile_id     = current_map.get_tile_id(current_location.level_index, target)

        interactable: Interactable = self.global_registry.interactables.get(target)      

        if interactable:
            interactable_moveinto_result = interactable.move_into()
            if interactable_moveinto_result.traversal_allowed == False and interactable_moveinto_result.alternative_action_taken == False:
                self._say_blocked()
            return interactable_moveinto_result

        # It's just regular terrain.
        terrain: Terrain = self.global_registry.terrains.get(target_tile_id)
        can_traverse_base_terrain = terrain.can_traverse(transport_mode, target_tile_id)

        if not can_traverse_base_terrain:
            self._say_blocked()

        return MoveIntoResult(
            traversal_allowed = can_traverse_base_terrain,
            alternative_action_taken = False
        )


    #
    # Player driven State transitions
    #

    def move(self, move_offset: Vector2):

        current_location = self.party_state.get_current_location()
        current_map: U5Map = self.global_registry.maps.get(current_location.location_index)
        target_location = current_location + move_offset

        # Handle out-of-bounds.
        if current_map.location_metadata.location_index == 0:
            # When in the overworld/underworld, wrap the coord because it's a globe.
            target_location.coord = current_map.get_wrapped_coord(target_location.coord)
        else:
            # When in a town/dungeon room/combat map etc, going out-of-bounds means exiting the map
            if not current_map.size_in_tiles.is_in_bounds(target_location.coord):
                self.party_state.pop_location()
                new_location = self.party_state.get_current_location()
                
                self._on_change_map_level(new_location.location_index, new_location.level_index)

                self.interactive_console.print_ascii(f"Exited {current_map.location_metadata.name.capitalize()}")
                return

        # Handle un-traversable terrain.
        if not self.can_traverse(target_location.coord).traversal_allowed:
            self._say_blocked()
            return

        # Move
        self.party_state.change_coord(target_location.coord)

        # map level change checks.
        target_tile_id = current_map.get_tile_id(current_location.level_index, target_location.coord)
        target_terrain: Terrain = self.global_registry.terrains.get(target_tile_id)
        new_level_index = current_location.level_index

        # entry points
        if target_terrain.entry_point == True:
            new_location: GlobalLocation = self.global_registry.entry_triggers.get(target_location)
            self.party_state.push_location(new_location)

            self._on_change_map_level(new_location.location_index, new_location.level_index)

            new_map: U5Map = self.global_registry.maps.get(new_location.location_index)
            self.interactive_console.print_ascii(f"Entered {new_map.location_metadata.name.capitalize()}")
            return

        # ladders                
        if target_terrain.move_up == True:
            new_level_index = target_location.level_index + 1

        if target_terrain.move_down == True:
            new_level_index = target_location.level_index - 1

        # stairs
        if target_terrain.stairs == True:
            # NOTE: This is just a guess, but seems to be working out ok.
            if current_location.level_index == current_map.location_metadata.default_level:
                new_level_index = current_map.location_metadata.default_level + 1
            else:
                new_level_index = current_map.location_metadata.default_level

        # update level if changed.
        if current_location.level_index != new_level_index:
            self.party_state.change_level(new_level_index)
            self._on_change_map_level(target_location.location_index, new_level_index)


        # Transport direction, and console message.
        if move_offset.x == 1:
            # east
            self.last_east_west = 0
            self.last_nesw_dir = 1
            msg = "East"
        elif move_offset.x == -1:
            # west
            self.last_east_west = 1
            self.last_nesw_dir = 3
            msg = "West"
        elif move_offset.y == 1:
            # south
            self.last_nesw_dir = 2
            msg = "South"
        elif move_offset.y == -1:
            # north
            self.last_nesw_dir = 0
            msg = "North"
            
        self.interactive_console.print_ascii(msg)

    def jimmy(self, direction: Vector2):

        target_coord = self.party_state.get_current_location().coord.add(direction)
        interactable: Interactable = self.global_registry.interactables.get(target_coord)      
        if interactable:
            interactable.jimmy()

    def ignite_torch(self):
        TORCH_RADIUS = 3
        TORCH_DURATION_HOURS = 4
        if self.party_inventory.get_quantity(InventoryOffset.TORCHES) == 0:
            self.interactive_console.print_ascii("No torches !")
            return
        self.interactive_console.print_ascii("Ignite torch !")
        self.party_inventory.add(InventoryOffset.TORCHES, -1)
        self.party_state.set_light(TORCH_RADIUS, self.world_clock.get_natural_time() + timedelta(hours = TORCH_DURATION_HOURS))

    def pass_time(self):
        if self.party_state.get_light_expiry() is None:
            return
        if self.world_clock.get_natural_time() > self.party_state.get_light_expiry():
            self.party_state.set_light(None, None)

    #
    # Testing only
    #

    def switch_outer_map(self):
        if self.party_state.get_current_location().location_index != 0:
            return
        if self.party_state.get_current_location().level_index == 0:        
            self.outer_map_level = 255 # underworld
        else:
            self.outer_map_level = 0   # britannia
    
    def rotate_transport(self):
        self.transport_mode = (self.transport_mode + 1) % len(self.global_registry.transport_modes)


