import pygame

from controllers.spell_controllers.coordinate_spell_controller import CoordinateSpellController
from controllers.spell_controllers.directional_spell_controller import DirectionalSpellController
from controllers.spell_controllers.general_spell_controller import GeneralSpellController
from controllers.spell_controllers.party_member_spell_controller import PartyMemberSpellController
from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.combat_map import CombatMap
from models.enums.spell_target_type import SpellTargetType
from models.party_inventory import PartyInventory
from models.spell_type import SpellType

from services.console_service import ConsoleService
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService
from services.input_service import InputService, keycode_to_char
from services.sfx_library_service import SfxLibraryService
from services.view_port_service import ViewPortService

INCUR_SPELL_COST = True
NO_SPELL_COST    = False

class CastController(DarkEventListenerMixin, LoggerMixin):

    console_service:   ConsoleService
    party_agent:       PartyAgent
    global_registry:   GlobalRegistry
    input_service: InputService
    party_inventory: PartyInventory
    
    info_panel_service:       InfoPanelService
    info_panel_data_provider: InfoPanelDataProvider
    sfx_library_service:      SfxLibraryService

    general_spell_controller:      GeneralSpellController
    party_member_spell_controller: PartyMemberSpellController
    directional_spell_controller:  DirectionalSpellController
    coordinate_spell_controller:   CoordinateSpellController

    view_port_service: ViewPortService

    def handle_event(self, event: pygame.event.Event, spell_caster: PartyMemberAgent, combat_map: CombatMap) -> bool:
        if event.key == pygame.K_c:
            self.cast(spell_caster, combat_map)
            return True
        else:
            return False

    def cast(self, spell_caster: PartyMemberAgent, combat_map: CombatMap):
        self._cast(spell_caster, combat_map)

        # Restore previous info panel state.
        party_data = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_data)

    def _cast(self, spell_caster: PartyMemberAgent, combat_map: CombatMap):
        self.console_service.print_ascii("Cast...", no_prompt = True)

        if spell_caster is None:
            spell_caster = self._get_spell_caster()
        if spell_caster is None:
            return

        rune_keys = self._read_spell_runes()

        if rune_keys is None:
            return

        self.console_service.print_ascii("", no_prompt = True)

        spell_type = self.global_registry.spell_types.get(rune_keys)

        if spell_type is None:
            self.log(f"DEBUG: Ignoring unknown spell key: {rune_keys}")
            self.console_service.print_ascii("No effect!")
            return

        incur_spell_cost = self._attempt_spell(spell_caster, spell_type, combat_map)

        #
        # TODO: If this is a potion or scroll, incur different costs.
        #
        if incur_spell_cost:
            spell_caster.mana = spell_caster.mana - spell_type.level
            self.party_inventory.use(spell_type.premix_inventory_offset)
            self.console_service.print_ascii("Success!")

    def _get_spell_caster(self) -> PartyMemberAgent:
        
        self.console_service.print_ascii("Player: ", include_carriage_return = False)

        party_data = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_data, select_mode = True)
        spell_caster_index = self.info_panel_service.choose_item(party_data.party_data_set, 0)

        if spell_caster_index is None:
            spell_caster = None
            self.console_service.print_ascii("None !")
        else:
            spell_caster = self.party_agent.get_party_member(spell_caster_index)
            self.console_service.print_ascii(spell_caster.name, no_prompt = True)

        self.info_panel_service.show_party_summary(party_data, select_mode = False)

        return spell_caster
        

    def _read_spell_runes(self) -> list[str]:

        self.console_service.print_ascii("Spell name:", no_prompt = True)
        self.console_service.print_ascii(":", include_carriage_return = False)

        rune_keys = ""

        while not self._has_quit:
            event = self.input_service.get_next_event()

            if event.key == pygame.K_ESCAPE or self._has_quit:
                self.console_service.print_ascii("None !")
                return None
            
            if event.key == pygame.K_RETURN:
                return rune_keys
            
            rune_key = keycode_to_char(event.key)
            if rune_key is None:
                continue

            rune_key = rune_key.lower()
            rune = self.global_registry.runes.get(rune_key)

            if rune is None:
                continue
            
            rune_keys += rune_key
            self.console_service.print_ascii(rune + " ", include_carriage_return = False)


    def _attempt_spell(self, spell_caster: PartyMemberAgent, spell_type: SpellType, combat_map: CombatMap):
        
        if (combat_map and not spell_type.combat_allowed) or (not combat_map and not spell_type.peace_allowed):
            self.console_service.print_ascii("Not here !")
            return NO_SPELL_COST

        if not self.party_inventory.has(spell_type.premix_inventory_offset):
            self.console_service.print_ascii("None mixed !")
            return NO_SPELL_COST

        insufficient_mana  = spell_caster.mana < spell_type.level
        insufficient_level = spell_caster.level < spell_type.level

        spell_caster.spend_action_quanta()

        if insufficient_mana or insufficient_level:
            self.console_service.print_ascii("Failed !")
            self.log(f"Spell failed: caster_mana={spell_caster.mana}, caster_level={spell_caster.level}, spell_level={spell_type.level}")
            return NO_SPELL_COST

        #
        # EVERY OBSTACLE OVERCOME - CAST THE DAMN SPELL ALREADY
        #

        if spell_type.target_type == SpellTargetType.T_NONE:
            return self.general_spell_controller.cast(spell_caster, spell_type)

        elif spell_type.target_type == SpellTargetType.T_DIRECTION:
            return self.directional_spell_controller.cast(combat_map, spell_caster, spell_type)

        elif spell_type.target_type == SpellTargetType.T_COORD:
            return self.coordinate_spell_controller.cast(combat_map, spell_caster, spell_type)

        elif spell_type.target_type == SpellTargetType.T_PARTY_MEMBER:
            return self.party_member_spell_controller.cast(spell_caster, spell_type)

        return INCUR_SPELL_COST

    



