from datetime import datetime

from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from models.global_location         import GlobalLocation
from models.enums.inventory_offset  import InventoryOffset

from data.global_registry           import GlobalRegistry
from data.global_registry_loader    import GlobalRegistryLoader

from controllers.display_controller import DisplayController
from controllers.party_controller   import PartyController
from services.map_cache.map_cache_service import MapCacheService
from services.world_clock           import WorldClock
from services.world_loot.world_loot_service import WorldLootService
from view.main_display              import MainDisplay

class InitialisationController(LoggerMixin):

    # Injectable
    global_registry_loader: GlobalRegistryLoader
    global_registry:        GlobalRegistry

    main_display: MainDisplay
    world_clock:  WorldClock
    world_loot_service: WorldLootService
    map_cache_service:  MapCacheService

    party_controller:   PartyController
    display_controller: DisplayController

    def init(self):
        
        self.global_registry_loader.load()

        self.display_controller.init()

#        self.saved_game_loader.load_existing()

        IOLOS_HUT = 13
        current_location = GlobalLocation(
            location_index = IOLOS_HUT,
            level_index    = 0,
            coord          = Coord(15, 15) # Inside the hut, OG starting position.
        )

        self.party_controller.load_inner_location(current_location)
        self.party_controller.load_transport_state(0,0,1) # on foot, "facing" east

        #
        # We pretend that we're loading a saved game at this world time.
        #
        self.world_clock.set_world_time(datetime(year=139, month=4, day=5, hour=23, minute=35))

        #
        # We pretend that we're loading a saved game with this inventory.
        #

        self.party_controller.load_party_inventory([
            (InventoryOffset.GOLD,   150),
            (InventoryOffset.FOOD,    63),
            (InventoryOffset.KEYS,    20),
            (InventoryOffset.TORCHES, 40)        
        ])

        self.world_loot_service.register_loot_containers()
        self.map_cache_service.init()

        self.log("Initialisation completed.")

