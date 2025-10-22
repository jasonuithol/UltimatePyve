import pygame

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.combat_map import CombatMap
from models.data_ovl import DataOVL
from models.enums.spell_target_type import SpellTargetType
from models.spell_type import SpellType

from services.console_service import ConsoleService
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService
from services.main_loop_service import MainLoopService, keycode_to_char


class CastController(DarkEventListenerMixin, LoggerMixin):

    console_service:   ConsoleService
    party_agent:       PartyAgent
    global_registry:   GlobalRegistry
    main_loop_service: MainLoopService
    data_ovl:          DataOVL
    
    info_panel_service:       InfoPanelService
    info_panel_data_provider: InfoPanelDataProvider
    
    def init(self):
        self._runes = {
            rune[0].lower() : rune
            for rune in DataOVL.to_strs(self.data_ovl.spell_runes) if len(rune) > 0
        } 
        self._spells = {
            "".join([rune[0].lower() for rune in spell_name.split(" ")]) : spell_name
            for spell_name in DataOVL.to_strs(self.data_ovl.spell_names) if len(spell_name) > 0
        }

    def handle_event(self, event: pygame.event.Event, spell_caster: PartyMemberAgent, combat_map: CombatMap):
        if event.key == pygame.K_c:
            self.cast(spell_caster, combat_map)

    def cast(self, spell_caster: PartyMemberAgent, combat_map: CombatMap):
        self._combat_map = combat_map
        self._spell_caster = spell_caster
        self._cast()

        # Restore previous info panel state.
        party_data = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_data)

    def _cast(self):
        self.console_service.print_ascii("Cast...", no_prompt = True)

        if self._spell_caster is None:
            self._spell_caster = self._get_spell_caster()
        if self._spell_caster is None:
            return

        rune_keys = self._read_spell_runes()

        if rune_keys is None:
            return

        self.console_service.print_ascii("", no_prompt = True)

        spell_type = self.global_registry.spell_types.get(rune_keys)

        if spell_type is None:
            self.console_service.print_ascii("No effect!")
            return

        self._attempt_spell(spell_type)

    def _get_spell_caster(self) -> PartyMemberAgent:
        
        self.console_service.print_ascii("Player: ", include_carriage_return = False)

        party_data = self.info_panel_data_provider.get_party_summary_data()
        self.info_panel_service.show_party_summary(party_data, select_mode = True)
        spell_caster_index = self.info_panel_service.choose_item(party_data.party_data_set, 0)

        if spell_caster_index is None:
            self.console_service.print_ascii("None !")
            return None
        else:
            spell_caster = self.party_agent.get_party_member(spell_caster_index)
            self.console_service.print_ascii(spell_caster.name, no_prompt = True)
            return spell_caster

    def _read_spell_runes(self) -> list[str]:

        self.console_service.print_ascii("Spell name:", no_prompt = True)

        rune_keys = ""

        while not self._has_quit:
            event = self.main_loop_service.get_next_event()

            if event.key == pygame.K_ESCAPE or self._has_quit:
                self.console_service.print_ascii("None !")
                return None
            
            if event.key == pygame.K_RETURN:
                return rune_keys
            
            rune_key = keycode_to_char(event.key)
            if rune_key is None:
                continue

            rune_key = rune_key.lower()
            rune = self._runes.get(rune_key, None)

            if rune is None:
                continue
            
            rune_keys += rune_key
            self.console_service.print_ascii(rune + " ", include_carriage_return = False)

    def _attempt_spell(self, spell_type: SpellType):
        
        if (self._combat_map and not spell_type.combat_allowed) or (not self._combat_map and not spell_type.peace_allowed):
            self.console_service.print_ascii("Not here !")
            return

        premixed_amount = self.global_registry.saved_game.read_u8(spell_type.premix_inventory_offset)
        if premixed_amount == 0:
            self.console_service.print_ascii("None mixed !")
            return

        insufficient_mana  = self._spell_caster.mana < spell_type.level
        insufficient_level = self._spell_caster.level < spell_type.level

        if insufficient_mana or insufficient_level:
            self.console_service.print_ascii("Failed !")
            self.log(f"Spell failed: caster_mana={self._spell_caster.mana}, caster_level={self._spell_caster.level}, spell_level={spell_type.level}")
            return

        if spell_type.target_type == SpellTargetType.T_DIRECTION:
            self.console_service.print_ascii("Direction: ", include_carriage_return = False)
            spell_direction = self.main_loop_service.obtain_action_direction()

        elif spell_type.target_type == SpellTargetType.T_COORD:
            #
            # TODO: Check if in combat mode
            #
            spell_coord = self.main_loop_service.obtain_cursor_position(
                starting_coord  = self._spell_caster.coord,
                boundary_rect   = self._combat_map.get_size().to_rect(Coord(0,0)),
                range_          = 255
            )

        elif spell_type.target_type == SpellTargetType.T_PARTY_MEMBER:
            self.console_service.print_ascii("On who: ", include_carriage_return = False)
            party_data = self.info_panel_data_provider.get_party_summary_data()
            self.info_panel_service.show_party_summary(party_data, select_mode = True)
            target_party_member_index = self.info_panel_service.choose_item(party_data.party_data_set, 0)


        self.log("Help ! I'm coooosting !!!")





