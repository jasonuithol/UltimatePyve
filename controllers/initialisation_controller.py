from pathlib import Path
from dark_libraries.logging   import LoggerMixin

from data.loaders.save_game_loader import SavedGameLoader
from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.enums.character_class_to_tile_id import CharacterClassToTileId

from data.global_registry           import GlobalRegistry
from data.global_registry_loader    import GlobalRegistryLoader

from controllers.party_controller   import PartyController
from models.enums.transport_mode import TransportMode
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService
from services.light_map_level_baker import LightMapLevelBaker
from services.map_cache.map_cache_service import MapCacheService
from services.sound_service import SoundService
from services.world_clock           import WorldClock
from services.world_loot.world_loot_service import WorldLootService
from view.info_panel import InfoPanel
from view.interactive_console import InteractiveConsole
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
    saved_game_loader: SavedGameLoader
    info_panel_service: InfoPanelService
    info_panel_data_provider: InfoPanelDataProvider
    info_panel: InfoPanel
    interactive_console: InteractiveConsole
    sound_service: SoundService


    def init(self, u5_path: Path):

        # Set's pygame screen/video mode.
        self.display_service.init()

        self.global_registry_loader.load(u5_path)

        # --------------------------------------------------
        #
        # LOAD A SAVED GAME
        #
        saved_game = self.saved_game_loader.load_existing(u5_path)
        self.global_registry.saved_game = saved_game
        #
        # --------------------------------------------------

        saved_location = saved_game.read_party_location()
        self.party_controller.load_location(saved_location)

        # TODO: read from saved_game
        self.party_controller.load_transport_state(TransportMode.WALK)

        self.world_clock.set_world_time(saved_game.read_current_datetime())
     

        for party_member_index in range(6):#range(saved_game.read_party_member_count()):

            character_record    = saved_game.create_character_record(party_member_index)
            char_tile_id        = CharacterClassToTileId.__dict__[character_record.char_class].value.value
            party_member_sprite = self.global_registry.sprites.get(char_tile_id)

            assert not party_member_sprite is None, f"Could not find sprite for tile_id={char_tile_id!r}"

            party_member = PartyMemberAgent(
                sprite           = party_member_sprite,
                character_record = character_record
            )
            party_member.global_registry = self.global_registry
            self.party_agent.party_members.append(party_member)

        # TODO: Incorporate saved game data
        self.world_loot_service.register_loot_containers()

        self.map_cache_service.init()
        self.light_map_level_baker.bake_level_light_maps()

        self.sound_service.init()

        #
        # Start displaying stuff
        #
        self.main_display.init()
        self.interactive_console.init()
        self.info_panel.init()
        self.info_panel_service.init()

        party_summary_data = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_summary_data)

        self.console_service.print_ascii("Returned to the world !")

        self.console_service.print_ascii("Gameplay keys", no_prompt=True)
        self.console_service.print_ascii("", no_prompt=True)
        self.console_service.print_ascii("A.. Attack", no_prompt=True)
        self.console_service.print_ascii("C.. Cast", no_prompt=True)
        self.console_service.print_ascii("I.. Ignite torch", no_prompt=True)
        self.console_service.print_ascii("J.. Jimmy lock", no_prompt=True)
        self.console_service.print_ascii("R.. Ready", no_prompt=True)
        self.console_service.print_ascii("1-6 Set default player", no_prompt=True)
        self.console_service.print_ascii("0.. Reset default player")

        self.console_service.print_ascii("Special keys", no_prompt=True)
        self.console_service.print_ascii("", no_prompt=True)
        self.console_service.print_ascii("F1. Host/quit multiplayer", no_prompt=True)
        self.console_service.print_ascii("F2. Join/quit multiplayer")

        self.log("Initialisation completed.")

