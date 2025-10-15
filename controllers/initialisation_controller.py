from datetime import datetime

from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.enums.character_class_to_tile_id import CharacterClassToTileId
from models.global_location         import GlobalLocation
from models.enums.inventory_offset  import InventoryOffset

from data.global_registry           import GlobalRegistry
from data.global_registry_loader    import GlobalRegistryLoader

from controllers.party_controller   import PartyController
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.light_map_level_baker import LightMapLevelBaker
from services.map_cache.map_cache_service import MapCacheService
from services.world_clock           import WorldClock
from services.world_loot.world_loot_service import WorldLootService
from view.main_display              import MainDisplay

class InitialisationController(LoggerMixin):

    # Injectable
    global_registry_loader: GlobalRegistryLoader
    global_registry:        GlobalRegistry
    party_agent:            PartyAgent

    main_display: MainDisplay
    world_clock:  WorldClock
    world_loot_service: WorldLootService
    map_cache_service:  MapCacheService

    party_controller: PartyController
    display_service:  DisplayService
    console_service: ConsoleService

    light_map_level_baker: LightMapLevelBaker

    def init(self):
        
        self.global_registry_loader.load()

        self.display_service.init()

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
        self.world_clock.set_world_time(datetime(year=139, month=4, day=5, hour=8, minute=35))

        #
        # We pretend that we're loading a saved game with this inventory.
        #

        self.party_controller.load_party_inventory([
            (InventoryOffset.GOLD,   150),
            (InventoryOffset.FOOD,    63),
            (InventoryOffset.KEYS,    20),
            (InventoryOffset.TORCHES, 40)        
        ])

        for party_member_index in range(6):

            character_record    = self.global_registry.saved_game.characters[party_member_index]
            char_tile_id        = CharacterClassToTileId.__dict__[character_record.char_class].value.value
            party_member_sprite = self.global_registry.sprites.get(char_tile_id)

            assert not party_member_sprite is None, f"Could not find sprite for tile_id={char_tile_id!r}"

            party_member = PartyMemberAgent(
                sprite           = party_member_sprite,
                character_record = character_record
            )
            party_member.global_registry = self.global_registry
            self.party_agent.party_members.append(party_member)

        self.world_loot_service.register_loot_containers()
        self.map_cache_service.init()
        self.light_map_level_baker.bake_level_light_maps()


        #
        # TODO: Remove once done
        #

        self.console_service.print_ascii("Returned to the world !")

        self.console_service.print_ascii(list(range(128)))
        self.console_service.print_runes(list(range(128)))

        self.log("Initialisation completed.")

