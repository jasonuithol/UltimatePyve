import math
import random

from dark_libraries.dark_math import Coord
from dark_libraries.dark_wave import DarkNote

from services.display_service import DisplayService
from services.sound_service import SoundService

from view.view_port import ViewPort

class SfxLibraryService:

    sound_service:   SoundService
    display_service: DisplayService
    view_port:       ViewPort

    def bubbling_of_reality(self):
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

    def emit_projectile(self):

        generator = self.sound_service.get_generator()

        start_hz = 1400.0
        end_hz   = 0.0
        duration = 0.125

#        sweep_down_modulator = generator.sawtooth_wave(geometry=-1.0).sequence([DarkNote(hz = duration * 16, sec = duration)])
        sweep_down_modulator = generator.sine_wave(phase_offset = math.pi / 2).sequence([DarkNote(hz = duration * 16, sec = duration)])
        whoosh_wave = generator.square_wave().sequence([DarkNote(hz = start_hz, sec = duration)]).frequency_modulate(
            sweep_down_modulator.wave_data, 
            base_hz = start_hz, 
            deviation_hz = start_hz - end_hz
        ).to_stereo()

        _, channel_handle = self.sound_service.play_sound(whoosh_wave)

        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            self.display_service.render()

    def damage(self, coord: Coord):
        # ANIMATION: Show The flashy explody tile.
        self.view_port.set_damage_blast_at(coord)

        # SOUND: "BBRRERRRKKCH"
        generator = self.sound_service.get_generator()
        noise_wave = generator.white_noise(hz = 1600.0, sec = 0.25).to_stereo()

        _, channel_handle = self.sound_service.play_sound(noise_wave)

        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            self.display_service.render()

        # ANIMATION: Hide The flashy explody tile.
        self.view_port.set_damage_blast_at(None)

    def cast_spell_normal(self):

        self.bubbling_of_reality()

        generator = self.sound_service.get_generator()

        # VISUAL: Invert all colors of the viewport
        self.view_port.invert_colors(True)

        # SOUND: The searing of the energy plane.


        generator = self.sound_service.get_generator()
        noise_wave = generator.white_noise(hz = 1600.0, sec = 2.0).clamp(-0.2, +0.2)

        duration = 2.0
        phase_shift = 1 / duration
        spell_wave_1 = generator.sawtooth_wave(geometry = -1.0).sequence([DarkNote(hz = 800.0, sec = 2.0)]).clamp(-0.4, +0.6).phaser()
        spell_wave_2 = generator.sawtooth_wave().sequence([DarkNote(hz = 951.0 - phase_shift, sec = 2.0)])
        spell_wave_3 = generator.sawtooth_wave().sequence([DarkNote(hz = 1131.0 - phase_shift * 2, sec = 2.0)])

        spell_wave_mixed = spell_wave_1.mix(spell_wave_2).mix(spell_wave_3)

        spell_wave = spell_wave_mixed.to_stereo().haas_widen(delay_seconds=0.02).stereo_phaser()        

        _, channel_handle = self.sound_service.play_sound(spell_wave)

        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            self.display_service.render()

        # VISUAL: Restore all colors of the viewport.
        self.view_port.invert_colors(False)
        return

    def cast_spell_projectile(self):
        # SOUND: The bubbling of the fabric of reality
        self.bubbling_of_reality()

        # SOUND: Whooshing of projectile.
        self.emit_projectile()

        # ANIMATION: Animate the movement of a glyph to the target.

        # if hit:

#            self._do_special_effects_impact()

        # else (a miss):

            # SOUND: "WHOOIIIP !"
            # ANIMATION: n/a

        return
