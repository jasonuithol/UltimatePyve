import random
from typing import Union
import pygame
import numpy as np
import numpy.typing as npt

from dark_libraries.dark_wave import DarkNote, DarkWave, DarkWaveGenerator, DarkWaveStereo, DarkWaveFloatArray, set_frequency_sample_rate as set_dark_wave_frequency_sample_rate
from dark_libraries.logging import LoggerMixin

NDArrayInt8  = npt.NDArray[np.int8]
NDArrayUInt8 = npt.NDArray[np.uint8]
NDArrayInt16 = npt.NDArray[np.int16]
NDArrayInt32 = npt.NDArray[np.int32]

# Sampled to the system's sample bit rate.
BitSampledWaveArrayType = Union[NDArrayInt8, NDArrayUInt8, NDArrayInt16, NDArrayInt32]

FADEIN_MILLISECONDS  = 5000
FADEOUT_MILLISECONDS = 5000

class SoundService(LoggerMixin):

    def init(self):
        pygame.mixer.init()
        self.frequency_sample_rate, self.sound_format, self.channels = pygame.mixer.get_init()
        self.log(
            f"Initialised pygame.mixer: " 
            + f"frequency_sample_rate={self.frequency_sample_rate}, "
            + f"sound_format={self.sound_format}, "
            + f"channels={self.channels}"
        )

        set_dark_wave_frequency_sample_rate(self.frequency_sample_rate)

        # Determine amplitude
        bits = abs(self.sound_format)
        signed = self.sound_format < 0
        if signed:
            self.amplitude_sampling_range = (2 ** (bits - 1)) - 1   # e.g. 32767 for 16‑bit signed
        else:
            self.amplitude_sampling_range = (2 ** bits) - 1         # e.g. 255 for 8‑bit unsigned

        self.log(f"Setting amplitude_sampling_range to {self.amplitude_sampling_range}")

        # Determining data type for output
        dtype_type: npt.DTypeLike = None
        if bits == 8:
            dtype_type = np.int8 if signed else np.uint8
        elif bits == 16:
            dtype_type = np.int16
        elif bits == 32:
            dtype_type = np.int32

        assert dtype_type, f"Unsupported bit depth: {bits}"

        self.log(f"Using output data type {dtype_type.__name__}")
        self.dtype = np.dtype(dtype_type)

        self.set_sfx_volume(0.35)
        self.set_soundtrack_volume(0.35)

    #
    # Volume Control
    #

    def set_sfx_volume(self, value: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, value))
        self.log(f"SFX volume set to {self.sfx_volume}")

    def get_sfx_volume(self) -> float:
        return self.sfx_volume

    def set_soundtrack_volume(self, value: float) -> None:
        self.soundtrack_volume = max(0.0, min(1.0, value))
        pygame.mixer.music.set_volume(self.soundtrack_volume)
        self.log(f"Soundtrack volume set to {self.soundtrack_volume}")

    def get_soundtrack_volume(self) -> float:
        return self.soundtrack_volume


    #
    # SFX & SFX Playback
    #

    def get_generator(self) -> DarkWaveGenerator:
        return DarkWaveGenerator()

    def _to_amplitude_sampled_wave(self, input_wave: DarkWaveFloatArray) -> BitSampledWaveArrayType:
        return (input_wave * self.amplitude_sampling_range).astype(self.dtype)
    
    def play_sound(self, input_wave: DarkWave | DarkWaveStereo) -> tuple[pygame.mixer.Sound, pygame.mixer.Channel]:

        #
        # TODO: automatically split/mix input into required output arity.
        #

        if isinstance(input_wave, DarkWaveStereo) and self.channels == 2:
            volume_adjusted = [
                channel * self.sfx_volume
                for channel in [input_wave.left, input_wave.right]
            ]

            channel_adjusted = np.column_stack((
                self._to_amplitude_sampled_wave(volume_adjusted[0]), 
                self._to_amplitude_sampled_wave(volume_adjusted[1]) 
            ))

        elif isinstance(input_wave, DarkWave) and self.channels == 1:
            volume_adjusted = input_wave.wave_data * self.sfx_volume
            channel_adjusted = self._to_amplitude_sampled_wave(volume_adjusted)

        else:
            assert False, f"Not implemented: input_wave is {type(input_wave).__name__} and channels={self.channels}"

        sound_handle = pygame.sndarray.make_sound(channel_adjusted)

        # non-blocking
        channel_handle = sound_handle.play()

        return sound_handle, channel_handle

    #
    # Background sound tracks played from file.
    #

    def play_music(self, path):
        if path is None:
            return
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(path)
        except pygame.error as e:
            self.log(f"ERROR: could not play background track at {path}: {e}")
            return
        pygame.mixer.music.set_volume(self.soundtrack_volume)
        pygame.mixer.music.play(loops = 0, fade_ms = FADEIN_MILLISECONDS)

    def stop_music(self):
        pygame.mixer.music.stop()

    def fade_music(self):
        pygame.mixer.music.fadeout(FADEOUT_MILLISECONDS)

#
# MAIN
#
if __name__ == "__main__":

    def _harmonic(base_hz, harmonic):
        return base_hz * 2**(harmonic / 12)
    
    def _wait(channel_handle):
        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            pygame.time.wait(1000)

        print("Channel no longer busy.")


    service = SoundService()
    service.init()
    generator = service.get_generator()

    do_tests = [
        False,  # pentatonic
        False,  # kaboom (more like a silent but deadly)
        False,  # spell casting noises
        False,  # cannonball
        False,  # projectile whoosh
        False,  # waterfall
        True    # projectile impact
    ]

    if do_tests[0]:

        print("TEST ONE - PENTATONIC")

        pentatonic_sequence = [
            DarkNote(_harmonic(base_hz = 440, harmonic = n), 0.5)
            for n in [0, 2, 4, 7, 9, 12]
        ]
        expected_duration = sum(note[1] for note in pentatonic_sequence)

        sawtooth_wave     = generator.sawtooth_wave().sequence(pentatonic_sequence).clamp(-0.4, +0.6)
        square_wave       = generator.square_wave().sequence(pentatonic_sequence).clamp(-0.4, +0.6)
        fm_modulated_wave = generator.fm_modulated_wave(mod_freq = 6.0, deviation_hz = 8.0).sequence(pentatonic_sequence).clamp(-0.4, +0.6)
        am_modulated_wave = generator.am_modulated_wave(mod_freq = 6.0, depth = 0.8).sequence(pentatonic_sequence).clamp(-0.4, +0.6)

        for sound_wave in [sawtooth_wave, square_wave, fm_modulated_wave, am_modulated_wave]: # [am_modulated_wave]: 

            normal = sound_wave.normalize_rms(target_rms = 0.1)
            stereo = normal.to_stereo().haas_widen()
            sound_handle, channel_handle = service.play_sound(stereo)

            print(f"Expected duration={expected_duration}, reported duration={sound_handle.get_length()}")

            _, channel_handle = service.play_sound(sound_wave)
            _wait(channel_handle)

    if do_tests[1]:

        print("TEST TWO - KABOOM!")

        # 1 second of noise
        noise_wave = generator.white_noise(1.0).clamp(-0.2, +0.6).normalize_rms()

        # Shape it

        # Add a low sine thump
        t = np.arange(len(noise_wave)) / service.frequency_sample_rate
        thump_wave: DarkWaveFloatArray = np.sin(2*np.pi*60*t) * np.exp(-t/0.6) # 60 Hz boom with 0.5s decay
        dark_thump = DarkWave(thump_wave)

        # Mix broadband
        blast_wave = noise_wave.mix(
            dark_thump
        ).normalize_rms().envelope(
            attack=0.005, 
            decay_fast=0.2, 
            decay_slow=1.0
        ).normalize_rms()
        '''
        ).phaser(
            stages=6, 
            lfo_hz=0.5, 
            feedback=0.4, 
            mix=0.8
        ).normalize_rms()
        '''

        stereo_blast_wave = blast_wave.to_stereo()

        _, channel_handle = service.play_sound(stereo_blast_wave)
        _wait(channel_handle)

        print("Channel no longer busy.")

    if do_tests[2]:

        print("TEST THREE - SPELL CASTING NOISES")

        bubbling_sequence = [
            DarkNote(hz = random.uniform(100.0, 800.0), sec = random.uniform(0.04, 0.12))
            for _ in range(16)
        ]

        cast_wave = generator.square_wave().sequence(bubbling_sequence).clamp(-0.4, +0.6).to_stereo()

        _, channel_handle = service.play_sound(stereo_blast_wave)
        _wait(channel_handle)

        duration = 2.0
        phase_shift = 1 / duration
        spell_wave_1 = generator.sawtooth_wave().sequence([DarkNote(hz = 800.0, sec = 2.0)]).clamp(-0.4, +0.6)
        spell_wave_2 = generator.sawtooth_wave().sequence([DarkNote(hz = 1600.0 - phase_shift, sec = 2.0)])
        
        spell_wave = spell_wave_1.to_stereo(left = spell_wave_2)        

        _, channel_handle = service.play_sound(spell_wave)
        _wait(channel_handle)

    if do_tests[3]:

        print("TEST FOUR - CANNON BALL !")

        start_hz = 400.0
        end_hz   = 0.0
        duration = 1.0

        sweep_down_modulator = generator.sawtooth_wave(geometry=-1.0).sequence([DarkNote(hz = duration, sec = duration)])
        whoosh_wave = generator.square_wave().sequence([DarkNote(hz = start_hz, sec = duration)]).frequency_modulate(
            sweep_down_modulator.wave_data, 
            base_hz = start_hz, 
            deviation_hz = start_hz - end_hz
        ).to_stereo()

        _, channel_handle = service.play_sound(whoosh_wave)
        _wait(channel_handle)


    if do_tests[4]:

        print("TEST FIVE - COMBAT PROJECTILE!")

        start_hz = 1400.0
        end_hz   = 200.0
        duration = 0.25

#        sweep_down_modulator = generator.sawtooth_wave(geometry=-1.0).sequence([DarkNote(hz = duration * 16, sec = duration)])
        sweep_down_modulator = generator.sine_wave(phase_offset = np.pi/2).sequence([DarkNote(hz = duration * 8, sec = duration)])
        whoosh_wave = generator.square_wave().sequence([DarkNote(hz = start_hz, sec = duration)]).frequency_modulate(
            sweep_down_modulator.wave_data, 
            base_hz = start_hz, 
            deviation_hz = start_hz - end_hz
        ).to_stereo()

        _, channel_handle = service.play_sound(whoosh_wave)
        _wait(channel_handle)


    if do_tests[5]:

        print("TEST SIX - WATERFALL!")

        noise_wave = generator.white_noise(hz = 20.0, sec = 2.0).to_stereo()

        _, channel_handle = service.play_sound(noise_wave)
        _wait(channel_handle)


    if do_tests[6]:

        print("TEST SIX - IMPACT!")

        noise_wave = generator.white_noise(hz = 1600.0, sec = 0.5).to_stereo()

        _, channel_handle = service.play_sound(noise_wave)
        _wait(channel_handle)
