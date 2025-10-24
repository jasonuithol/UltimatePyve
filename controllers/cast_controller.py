import math
import random
import pygame

from controllers.spell_controllers.general_spell_controller import GeneralSpellController
from controllers.spell_controllers.party_member_spell_controller import PartyMemberSpellController
from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math import Coord
from dark_libraries.dark_wave import DarkNote
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.combat_map import CombatMap
from models.data_ovl import DataOVL
from models.enums.spell_target_type import SpellTargetType
from models.spell_type import SpellType

from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.info_panel_data_provider import InfoPanelDataProvider
from services.info_panel_service import InfoPanelService
from services.main_loop_service import MainLoopService, keycode_to_char
from services.sound_service import SoundService
from view.view_port import ViewPort

INCUR_SPELL_COST = True
NO_SPELL_COST    = False

class CastController(DarkEventListenerMixin, LoggerMixin):

    console_service:   ConsoleService
    party_agent:       PartyAgent
    global_registry:   GlobalRegistry
    main_loop_service: MainLoopService
    data_ovl:          DataOVL
    
    info_panel_service:       InfoPanelService
    info_panel_data_provider: InfoPanelDataProvider

    general_spell_controller: GeneralSpellController
    party_member_spell_controller: PartyMemberSpellController
    sound_service: SoundService

    display_service: DisplayService
    view_port: ViewPort

    def handle_event(self, event: pygame.event.Event, spell_caster: PartyMemberAgent, combat_map: CombatMap):
        if event.key == pygame.K_c:
            self.cast(spell_caster, combat_map)

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
            self.console_service.print_ascii("No effect!")
            return

        incur_spell_cost = self._attempt_spell(spell_caster, spell_type, combat_map)

        #
        # TODO: If this is a potion or scroll, incur different costs.
        #
        if incur_spell_cost:
            spell_caster.mana = spell_caster.mana - spell_type.level
            premixed_amount = self._get_premixed_amount(spell_type)
            self._set_premixed_amount(spell_type, premixed_amount - 1)
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
            rune = self.global_registry.runes.get(rune_key)

            if rune is None:
                continue
            
            rune_keys += rune_key
            self.console_service.print_ascii(rune + " ", include_carriage_return = False)


    def _attempt_spell(self, spell_caster: PartyMemberAgent, spell_type: SpellType, combat_map: CombatMap):
        
        if (combat_map and not spell_type.combat_allowed) or (not combat_map and not spell_type.peace_allowed):
            self.console_service.print_ascii("Not here !")
            return NO_SPELL_COST

        premixed_amount = self._get_premixed_amount(spell_type)
        if premixed_amount == 0:
            self.console_service.print_ascii("None mixed !")
            return NO_SPELL_COST

        insufficient_mana  = spell_caster.mana < spell_type.level
        insufficient_level = spell_caster.level < spell_type.level

        if insufficient_mana or insufficient_level:
            self.console_service.print_ascii("Failed !")
            self.log(f"Spell failed: caster_mana={spell_caster.mana}, caster_level={spell_caster.level}, spell_level={spell_type.level}")
            return NO_SPELL_COST

        if spell_type.target_type == SpellTargetType.T_NONE:
            self._do_special_effects_normal()
            self.general_spell_controller.cast(spell_caster, spell_type)

        elif spell_type.target_type == SpellTargetType.T_DIRECTION:
            self.console_service.print_ascii("Direction: ", include_carriage_return = False)
            spell_direction = self.main_loop_service.obtain_action_direction()
            self._do_special_effects_normal()

        elif spell_type.target_type == SpellTargetType.T_COORD:

            assert combat_map, "Should be in combat, or have been prevented from casting this spell"

            spell_coord = self.main_loop_service.obtain_cursor_position(
                starting_coord  = spell_caster.coord,
                boundary_rect   = combat_map.get_size().to_rect(Coord(0,0)),
                range_          = 255
            )
            self._do_special_effects_coord()

        elif spell_type.target_type == SpellTargetType.T_PARTY_MEMBER:

            self.console_service.print_ascii("On who: ", include_carriage_return = False)
            party_data = self.info_panel_data_provider.get_party_summary_data()
            self.info_panel_service.show_party_summary(party_data, select_mode = True)

            target_party_member_index = self.info_panel_service.choose_item(party_data.party_data_set, 0)
            target_party_member = self.party_agent.get_party_member(target_party_member_index)
            self.console_service.print_ascii(target_party_member.name, no_prompt = True)

            self._do_special_effects_normal()
            self.party_member_spell_controller.cast(spell_caster, spell_type, target_party_member)

        return INCUR_SPELL_COST

    def _get_premixed_amount(self, spell_type: SpellType) -> int:
        return self.global_registry.saved_game.read_u8(spell_type.premix_inventory_offset)

    def _set_premixed_amount(self, spell_type: SpellType, amount: int) -> int:
        return self.global_registry.saved_game.write_u8(spell_type.premix_inventory_offset, amount)
    

    def _do_special_effects_bubbling_of_reality(self):
        # SOUND: The bubbling of the fabric of reality
        generator = self.sound_service.get_generator()

        bubbling_sequence = [
            DarkNote(hz = random.uniform(100.0, 800.0), sec = random.uniform(0.04, 0.12))
            for _ in range(16)
        ]

        cast_wave = generator.square_wave().sequence(bubbling_sequence).clamp(-0.4, +0.6).to_stereo()

        _, channel_handle = self.sound_service.play_sound(cast_wave)

        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            self.display_service.render()

    def _do_special_effects_projectile(self):

        generator = self.sound_service.get_generator()

        start_hz = 1400.0
        end_hz   = 200.0
        duration = 0.25

#        sweep_down_modulator = generator.sawtooth_wave(geometry=-1.0).sequence([DarkNote(hz = duration * 16, sec = duration)])
        sweep_down_modulator = generator.sine_wave(phase_offset = math.pi / 2).sequence([DarkNote(hz = duration * 8, sec = duration)])
        whoosh_wave = generator.square_wave().sequence([DarkNote(hz = start_hz, sec = duration)]).frequency_modulate(
            sweep_down_modulator.wave_data, 
            base_hz = start_hz, 
            deviation_hz = start_hz - end_hz
        ).to_stereo()

        _, channel_handle = self.sound_service.play_sound(whoosh_wave)

        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            self.display_service.render()

    def _do_special_effects_normal(self):

        self._do_special_effects_bubbling_of_reality()

        generator = self.sound_service.get_generator()

        # VISUAL: Invert all colors of the viewport
        self.view_port.invert_colors(True)

        # SOUND: The searing of the energy plane.

        duration = 2.0
        phase_shift = 1 / duration
        spell_wave_1 = generator.sawtooth_wave().sequence([DarkNote(hz = 800.0, sec = 2.0)]).clamp(-0.4, +0.6)
        spell_wave_2 = generator.sawtooth_wave().sequence([DarkNote(hz = 1600.0 - phase_shift, sec = 2.0)])
        
        spell_wave = spell_wave_1.to_stereo(left = spell_wave_2)        

        _, channel_handle = self.sound_service.play_sound(spell_wave)

        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            self.display_service.render()

        # VISUAL: Restore all colors of the viewport.
        self.view_port.invert_colors(False)
        return

    def _do_special_effects_coord(self):
        # SOUND: The bubbling of the fabric of reality
        self._do_special_effects_bubbling_of_reality()

        # SOUND: Whooshing of projectile.
        self._do_special_effects_projectile()

        # ANIMATION: Animate the movement of a glyph to the target.

        # if hit:

            # SOUND: "BBRRERRRKKCH"
            # ANIMATION: The flashy explody tile.

        # else (a miss):

            # SOUND: "WHOOIIIP !"
            # ANIMATION: n/a

        return



