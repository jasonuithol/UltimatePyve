# file: game/player_state.py
from typing import Tuple

from dark_libraries.dark_math import Coord, Vector2

from display.interactive_console import InteractiveConsole
from items.item_type import InventoryOffset
from maps import U5Map, U5MapRegistry
from items import PartyInventory, InventoryOffset

from .interactable.interactable import Interactable, MoveIntoResult
#from .saved_game import SavedGame
from .interactable.interactable_factory_registry import InteractableFactoryRegistry
from .map_transitions import get_entry_trigger
from .terrain import TerrainRegistry
from .transport_mode_registry import TransportModeRegistry

class PlayerState:

    # Injectable
    u5map_registry: U5MapRegistry
    interactable_factory_registry: InteractableFactoryRegistry
    terrain_registry: TerrainRegistry
    transport_mode_registry: TransportModeRegistry
    party_inventory: PartyInventory
    interactive_console: InteractiveConsole

    # either "britannia" or "underworld"
    outer_map: U5Map = None
    outer_map_level: int = None          
    outer_coord: Coord = None

    inner_map: U5Map = None
    inner_map_level: int = None
    inner_coord: Coord = None

    # options: walk, horse, carpet, skiff, ship
    transport_mode: int = None
    last_east_west: int = None
    last_nesw_dir: int = None

    def set_outer_position(self, u5Map: U5Map, level_index: int, coord: Coord):

        self.outer_map = u5Map
        self.outer_map_level = level_index
        self.outer_coord = coord

    def set_inner_position(self, u5Map: U5Map, level_index: int, coord: Coord):

        self.inner_map = u5Map
        self.inner_map_level = level_index
        self.inner_coord = coord

    def set_transport_state(self, transport_mode: int, last_east_west: int, last_nesw_dir: int):
        self.transport_mode = transport_mode
        self.last_east_west = last_east_west
        self.last_nesw_dir = last_nesw_dir

    def is_in_outer_map(self) -> bool:
        return self.inner_map is None

    def get_current_position(self) -> Tuple[U5Map, int, Coord]:
        if self.is_in_outer_map():
            return self.outer_map, 0, self.outer_coord
        else:
            return self.inner_map, self.inner_map_level, self.inner_coord

    def get_current_transport_info(self) -> Tuple[int, int]:
        if self.transport_mode == 0:
            direction = 0 # no one cares.
        elif self.transport_mode < 3:
            direction = self.last_east_west
        else:
            direction = self.last_nesw_dir

        return self.transport_mode, direction

    def _can_traverse(self, target: Coord) -> MoveIntoResult:
        transport_mode = self.transport_mode_registry.get_transport_mode(self.transport_mode)
        current_map, current_level, _ = self.get_current_position()
        target_tile_id = current_map.get_tile_id(current_level, target)
        interactable: Interactable = self.interactable_factory_registry.get_interactable(target)      

        if interactable:
            #
            # TODO: If you walk into a closed loot container, open it.
            #       If you walk into an open loot container, take the top item.
            #       If you walk into an empty loot container, raise an error.
            #
            interactable_moveinto_result = interactable.move_into()
            if interactable_moveinto_result.traversal_allowed == False and interactable_moveinto_result.alternative_action_taken == False:
                self._blocked()
            return interactable_moveinto_result

        # It's just regular terrain.
        can_traverse_base_terrain = self.terrain_registry.can_traverse(transport_mode, target_tile_id)

        if not can_traverse_base_terrain:
            self._blocked()

        return MoveIntoResult(
            traversal_allowed = can_traverse_base_terrain,
            alternative_action_taken = False
        )

    #
    # Internal State transitions
    #

    def _on_changing_map(self, location_index: int, level_index: int) -> None:
        self.interactable_factory_registry.load_level(location_index, level_index)

    def _move_to_inner_map(self, u5map: U5Map):
        self.inner_map = u5map
        self.inner_coord = Coord(
            (u5map.size_in_tiles.w - 1) // 2,
            (u5map.size_in_tiles.h - 2)
        )
        self._move_to_inner_map_level(u5map.location_metadata.default_level)
        self.interactive_console.print_ascii(f"Entered {u5map.location_metadata.name.capitalize()}")

    def _move_to_inner_map_level(self, level_index: int):
        self.inner_map_level = level_index
        self._on_changing_map(self.inner_map.location_metadata.location_index, level_index)

    def _return_to_outer_map(self):
        self.interactive_console.print_ascii(f"Exited {self.inner_map.location_metadata.name.capitalize()}")

        self.inner_map = None
        self.inner_map_level = None
        self.inner_coord = None
        self._on_changing_map(self.outer_map.location_metadata.location_index, self.outer_map_level)

    #
    # Player driven State transitions
    #

    def _blocked(self):
        self.interactive_console.print_ascii("Blocked !")

    def move(self, value: Vector2):

        #
        # Check map transitions
        #

        if self.is_in_outer_map():
            target = self.outer_coord.add(value)
            target = self.outer_map.get_wrapped_coord(target)

            # Check traversability before transitions.
            # A ship cannot enter a town, for example, so we must forbid it here.
            if not self._can_traverse(target).traversal_allowed:
                return

            # Move            
            self.outer_coord = target

            # Check map transitions
            trigger_index = get_entry_trigger(target)
            if trigger_index:
                inner_map = self.u5map_registry.get_map_by_trigger_index(trigger_index)
                # always succeeds.
                return self._move_to_inner_map(inner_map)

        else:
            target = self.inner_coord.add(value)
            if not self.inner_map.is_in_bounds(target):
                self._return_to_outer_map()
                return

            if not self._can_traverse(target).traversal_allowed:
                return
                
            # Move            
            self.inner_coord = target

            # Check for map level changes.
            tile_id = self.inner_map.get_tile_id(self.inner_map_level, self.inner_coord)
            terrain = self.terrain_registry.get_terrain(tile_id)
            if terrain.move_up == True:
                self._move_to_inner_map_level(self.inner_map_level + 1)
            if terrain.move_down == True:
                self._move_to_inner_map_level(self.inner_map_level - 1)

            # NOTE: This is a guess.
            if terrain.stairs == True:
                if self.inner_map_level == self.inner_map.location_metadata.default_level:
                    self._move_to_inner_map_level(self.inner_map_level + 1)
                else:
                    self._move_to_inner_map_level(self.inner_map_level - 1)

        if value.x == 1:
            # east
            self.last_east_west = 0
            self.last_nesw_dir = 1
            msg = "East"
        elif value.x == -1:
            # west
            self.last_east_west = 1
            self.last_nesw_dir = 3
            msg = "West"
        elif value.y == 1:
            # south
            self.last_nesw_dir = 2
            msg = "South"
        elif value.y == -1:
            # north
            self.last_nesw_dir = 0
            msg = "North"

        self.interactive_console.print_ascii(msg)

    def jimmy(self, direction: Vector2):

        if self.is_in_outer_map():
            return
        if self.party_inventory.get_quantity(InventoryOffset.KEYS) == 0:
            self.interactive_console.print_ascii("No keys !")
            return

        target = self.inner_coord.add(direction)
        interactable: Interactable = self.interactable_factory_registry.get_interactable(target)      
        if interactable:
            interactable.jimmy()

    #
    # Testing only
    #

    def switch_outer_map(self):
        if self.outer_map_level == 0:
            self.outer_map_level = 255 # underworld
        else:
            self.outer_map_level = 0   # britannia
    
    def rotate_transport(self):
        self.transport_mode = (self.transport_mode + 1) % len(self.transport_mode_registry._transport_modes)
        

