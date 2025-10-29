import math
import random

import pygame

from dark_libraries.dark_math import ORIGIN, Coord, Rect, Vector2
from dark_libraries.dark_wave import DarkNote, DarkWave, DarkWaveStereo

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.enums.direction_map import DIRECTION_SECTORS
from models.enums.ega_palette_values import EgaPaletteValues
from models.enums.projectile_type import ProjectileType
from models.magic_ray_set import MagicRaySet
from models.motion import Motion
from models.projectile import Projectile
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.input_service import InputService
from services.sound_service import SoundService

from services.view_port_service import ViewPortService
from view.display_config import DisplayConfig

# This can be anything we want really.
PROJECTILE_SPATIAL_UNITS_PER_SECOND = 11 # in tiles
BIBLICALLY_ACCURATE_CONE_OF_MAGIC_RAY_LENGTH_INCREMENT_IN_TILES = 0.5
NUMBER_OF_MAGIC_RAYS_IN_CONE_OF_MAGIC = 20
SECONDS_BETWEEN_RAY_GROWTHS = 0.05 / NUMBER_OF_MAGIC_RAYS_IN_CONE_OF_MAGIC

def _harmonic(base_hz, harmonic) -> float:
    return base_hz * 2**(harmonic / 12)

def _shortest_span(start: float, end: float) -> float:
    """Return the signed shortest angular difference in radians."""
    diff = (end - start) % (2 * math.pi)
    if diff > math.pi:
        diff -= 2 * math.pi
    return diff

class SfxLibraryService(LoggerMixin):

    display_config:  DisplayConfig
    global_registry: GlobalRegistry
    sound_service:   SoundService
    display_service: DisplayService
    view_port_service: ViewPortService
    console_service: ConsoleService
    input_service:   InputService

    def _play_and_wait(self, dark_wave: DarkWave | DarkWaveStereo):

        _, channel_handle = self.sound_service.play_sound(dark_wave)

        # Keep rendering until the sound finished, but don't take any more input
        while channel_handle.get_busy():
            self.display_service.render()
            self.input_service.discard_events()

    def _wait_seconds(self, seconds: float):
        deadline_ticks = pygame.time.get_ticks() + (seconds * 1000)
        while pygame.time.get_ticks() < deadline_ticks:
            self.display_service.render()
            self.input_service.discard_events()

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

        while not projectile.can_stop():
            self.display_service.render()

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

    def victory(self):
        generator = self.sound_service.get_generator()
        victory_wave = generator.square_wave().sequence([
            #
            # TODO: These need to be chords of some sort
            #

            DarkNote(440, 0.5),
            DarkNote(  0, 0.1),
            DarkNote(440, 0.5),
            DarkNote(  0, 0.1),
            DarkNote(440, 0.5),
            DarkNote(  0, 0.1),
            DarkNote(_harmonic(440, 5), 0.75), # Obviously needs to be some major fifth thingo.
        ]).to_stereo()

        self._play_and_wait(victory_wave)

    def cone_of_magic(self, start_coord: Coord, spell_direction: Vector2[int], color: EgaPaletteValues, ray_boundaries: Rect[int]):

        # Build the ray animation, but don't play it yet.
        magic_ray_set_playlist = self._build_magic_ray_set_playlist(start_coord, spell_direction, color, ray_boundaries)

        # Just make this something ridiculously too long
        playlist_duration_seconds = 10.0

        # SOUND: A directional cone of magic rays
        generator = self.sound_service.get_generator()
        noise_wave = generator.white_noise(hz = 1200.0, sec = playlist_duration_seconds).to_stereo()

        # Fire and forget, allowing this sound, and the following animation to play simultaneously
        _, noise_handle = self.sound_service.play_sound(noise_wave)

        # ANIMATION: Now we play the rays fanning out from the spell-caster.
        for magic_ray_set in magic_ray_set_playlist:
            self._wait_seconds(SECONDS_BETWEEN_RAY_GROWTHS)
            self.view_port_service.set_magic_rays(magic_ray_set)

        # Once the animation is finished, halt the sound effect.
        noise_handle.stop()

        self.log(f"DEBUG: Magic ray finished.  Endpoints stopped at {magic_ray_set.end_points}")

    def _build_magic_ray_set_playlist(self, start_coord: Coord, spell_direction: Vector2[int], color: EgaPaletteValues, ray_boundaries: Rect[int]) -> list[MagicRaySet]:

        ray_angles = self._build_magic_ray_angles(spell_direction)

        unfinished_magic_rays = {
            ray_angle : (0.0, start_coord)
            for ray_angle in ray_angles
        }

        finished_magic_rays = {}

        play_list = list[MagicRaySet]()

        while any(unfinished_magic_rays):

            ray_angle, ray_state = random.choice([x for x in unfinished_magic_rays.items()])
            current_length, current_end_coord = ray_state

            new_length = current_length + BIBLICALLY_ACCURATE_CONE_OF_MAGIC_RAY_LENGTH_INCREMENT_IN_TILES
            new_end_offset = ORIGIN.from_polar_coords(ray_angle, new_length).math_to_screen()
            new_end_coord = start_coord + new_end_offset

            self.log(f"DEBUG: Growing magic ray angle={ray_angle}, length={current_length} -> {new_length}, end_coord={current_end_coord} -> {new_end_coord}")

            # This check requires that the unit of length is TILES.
            if ray_boundaries.is_in_bounds(new_end_coord):
                unfinished_magic_rays[ray_angle] = (new_length, new_end_coord)
            else:
                self.log(f"DEBUG: Terminating growth of magic ray angle={ray_angle}, length={new_length}, end_coord={new_end_coord}")
                # The ray has finished growing
                del unfinished_magic_rays[ray_angle]
                # ... but must still remain visible.
                finished_magic_rays[ray_angle] = (new_length, new_end_coord)

            magic_ray_set = MagicRaySet(
                origin = start_coord,
                end_points = [
                    ray_state[1] # new_end_coord
                    for _, ray_state in (unfinished_magic_rays | finished_magic_rays).items()
                ],
                color = color
            )

            play_list.append(magic_ray_set)

        return play_list

    def _build_magic_ray_angles(self, spell_direction: Vector2[int]) -> list[float]:

        #
        # TODO: This is going be embodied in some extensions to dark_math once I get my head around it properly
        #

        # ANIMATION: Draw a rapidly expanding cone of magic originating from the origin
        min_normal_screen, max_normal_screen = DIRECTION_SECTORS[spell_direction]

        min_normal = min_normal_screen.screen_to_math()
        max_normal = max_normal_screen.screen_to_math()

        min_angle_radians = ORIGIN.angle_radians(min_normal) % (2 * math.pi) 
        max_angle_radians = ORIGIN.angle_radians(max_normal) % (2 * math.pi)

        self.log(f"DEBUG: Casting ray angles from {min_angle_radians} radians (normal={min_normal}) to {max_angle_radians} radians (normal={max_normal})")

        # can be positive or negative
        ray_angle_span = _shortest_span(min_angle_radians, max_angle_radians)
        self.log(f"DEBUG: ray_angle_span={ray_angle_span}")

        ray_angle_delta = ray_angle_span / NUMBER_OF_MAGIC_RAYS_IN_CONE_OF_MAGIC
        self.log(f"DEBUG: ray_angle_delta={ray_angle_delta}")

        ray_angles = [
            (min_angle_radians + (ray_angle_delta * ray_index)) % (2 * math.pi)
            for ray_index in range(NUMBER_OF_MAGIC_RAYS_IN_CONE_OF_MAGIC + 1)
        ]

        self.log(f"DEBUG: built magic ray angles={ray_angles}")

        return ray_angles
                    
