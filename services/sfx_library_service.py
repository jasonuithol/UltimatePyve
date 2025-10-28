import math
import random

from dark_libraries.dark_math import Coord
from dark_libraries.dark_wave import DarkNote, DarkWave, DarkWaveStereo

from data.global_registry import GlobalRegistry
from models.enums.projectile_type import ProjectileType
from models.motion import Motion
from models.projectile import Projectile
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.sound_service import SoundService

from services.view_port_service import ViewPortService
from view.display_config import DisplayConfig

# This can be anything we want really.
PROJECTILE_SPATIAL_UNITS_PER_SECOND = 11 # in tiles

class SfxLibraryService:

    display_config:  DisplayConfig
    global_registry: GlobalRegistry
    sound_service:   SoundService
    display_service: DisplayService
    view_port_service: ViewPortService
    console_service: ConsoleService

    def _play_and_wait(self, dark_wave: DarkWave | DarkWaveStereo):

        _, channel_handle = self.sound_service.play_sound(dark_wave)

        # Keep rendering until the sound finished, but don't take any more input
        while channel_handle.get_busy():
            self.display_service.render()

    def _create_motion(self, start_tile_coord: Coord[int], finish_tile_coord: Coord[int]) -> Motion:
        return Motion(
            start_tile_coord, 
            finish_tile_coord, 
            PROJECTILE_SPATIAL_UNITS_PER_SECOND
        )

    def bubbling_of_reality(self):
        # SOUND: The bubbling of the fabric of reality
        generator = self.sound_service.get_generator()

        bubbling_sequence = [
            DarkNote(hz = random.uniform(100.0, 800.0), sec = random.uniform(0.04, 0.12))
            for _ in range(16)
        ]

        cast_wave = generator.square_wave().sequence(bubbling_sequence).clamp(-0.4, +0.6).to_stereo()
        self._play_and_wait(cast_wave)

    def emit_projectile(self, projectile_type: ProjectileType, start_world_coord: Coord[int], finish_world_coord: Coord[int]):

        # ANIMATION: Kick-off a projectile
        sprite = self.global_registry.projectile_sprites.get(projectile_type)
        motion = self._create_motion(start_world_coord, finish_world_coord)
        projectile = Projectile(sprite, motion)

#        self.console_service.print_glyphs(sprite.frames)

        self.view_port_service.start_projectile(projectile)

        # SOUND: Pee yow !
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

        self._play_and_wait(whoosh_wave)

    def damage(self, coord: Coord[int]):
        # ANIMATION: Show The flashy explody tile.
        self.view_port_service.set_damage_blast_at(coord)

        # SOUND: "BBRRERRRKKCH"
        generator = self.sound_service.get_generator()
        noise_wave = generator.white_noise(hz = 1600.0, sec = 0.25).to_stereo()

        self._play_and_wait(noise_wave)

        # ANIMATION: Hide The flashy explody tile.
        self.view_port_service.set_damage_blast_at(None)

    def cast_spell_normal(self):

        self.bubbling_of_reality()

        generator = self.sound_service.get_generator()

        # VISUAL: Invert all colors of the viewport
        self.view_port_service.invert_colors(True)

        # SOUND: The searing of the energy plane.


        generator = self.sound_service.get_generator()
#        noise_wave = generator.white_noise(hz = 1600.0, sec = 2.0).clamp(-0.2, +0.2)

        duration = 2.0
        phase_shift = 1 / duration
        spell_wave_1 = generator.sawtooth_wave(geometry = -1.0).sequence([DarkNote(hz = 800.0, sec = 2.0)]).clamp(-0.4, +0.6).phaser()
        spell_wave_2 = generator.sawtooth_wave().sequence([DarkNote(hz = 951.0 - phase_shift, sec = 2.0)])
        spell_wave_3 = generator.sawtooth_wave().sequence([DarkNote(hz = 1131.0 - phase_shift * 2, sec = 2.0)])

        spell_wave_mixed = spell_wave_1.mix(spell_wave_2).mix(spell_wave_3)

        spell_wave = spell_wave_mixed.to_stereo().haas_widen(delay_seconds=0.02).stereo_phaser()        

        self._play_and_wait(spell_wave)

        # VISUAL: Restore all colors of the viewport.
        self.view_port_service.invert_colors(False)
        return

    def cast_spell_projectile(self):
        # SOUND: The bubbling of the fabric of reality
        self.bubbling_of_reality()

        # SOUND: Whooshing of projectile.

        # ANIMATION: Animate the movement of a glyph to the target.

        # if hit:

#            self._do_special_effects_impact()

        # else (a miss):

            # SOUND: "WHOOIIIP !"
            # ANIMATION: n/a

        return
    
    def victory(self):
        generator = self.sound_service.get_generator()
        victory_wave = generator.square_wave().sequence([
            DarkNote(440, 0.5),
            DarkNote(  0, 0.1),
            DarkNote(440, 0.5),
            DarkNote(  0, 0.1),
            DarkNote(440, 0.5),
            DarkNote(  0, 0.1),
            DarkNote(440 * 2, 0.75),
        ]).to_stereo()

        self._play_and_wait(victory_wave)
