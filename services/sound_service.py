import pygame
import numpy

from dark_libraries.dark_wave import BitSampledWaveArrayType, DarkWaveGenerator, DarkWaveStereo, RawValueWaveArrayType
from dark_libraries.logging import LoggerMixin

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

        # Determine amplitude
        bits = abs(self.sound_format)
        signed = self.sound_format < 0
        if signed:
            self.amplitude_sampling_range = (2 ** (bits - 1)) - 1   # e.g. 32767 for 16‑bit signed
        else:
            self.amplitude_sampling_range = (2 ** bits) - 1         # e.g. 255 for 8‑bit unsigned

        self.log(f"Setting amplitude_sampling_range to {self.amplitude_sampling_range}")

        # Determining data type for output
        dtype_type: numpy.typing.DTypeLike = None
        if bits == 8:
            dtype_type = numpy.int8 if signed else numpy.uint8
        elif bits == 16:
            dtype_type = numpy.int16
        elif bits == 32:
            dtype_type = numpy.int32

        assert dtype_type, f"Unsupported bit depth: {bits}"

        self.log(f"Using output data type {dtype_type.__name__}")
        self.dtype = numpy.dtype(dtype_type)

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
        return DarkWaveGenerator(self.frequency_sample_rate)

    def _to_amplitude_sampled_wave(self, input_wave: RawValueWaveArrayType) -> BitSampledWaveArrayType:
        return (input_wave * self.amplitude_sampling_range).astype(self.dtype)
    
    def play_sound(self, input_wave: DarkWaveStereo) -> tuple[pygame.mixer.Sound, pygame.mixer.Channel]:

        if self.channels == 2:
            volume_adjusted = [
                channel * self.sfx_volume
                for channel in [input_wave.left, input_wave.right]
            ]

            channel_adjusted = numpy.column_stack((
                self._to_amplitude_sampled_wave(volume_adjusted[0]), 
                self._to_amplitude_sampled_wave(volume_adjusted[1]) 
            ))
        else:
             assert False, "Not supported yet"

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

    service = SoundService()
    service.init()

    print("TEST ONE - PENTATONIC")

    pentatonic_sequence = [
        (440 * 2**(n / 12), 0.5)
        for n in [0, 2, 4, 7, 9, 12]
    ]
    expected_duration = sum(note[1] for note in pentatonic_sequence)

    generator = service.get_generator()

    sawtooth_wave     = generator.sawtooth_wave().sequence(pentatonic_sequence).clamp(-0.4, +0.6)
    square_wave       = generator.square_wave().sequence(pentatonic_sequence).clamp(-0.4, +0.6)
    fm_modulated_wave = generator.fm_modulated_wave(mod_freq = 6.0, deviation_hz = 8.0).sequence(pentatonic_sequence).clamp(-0.4, +0.6)
    am_modulated_wave = generator.am_modulated_wave(mod_freq = 6.0, depth = 0.8).sequence(pentatonic_sequence).clamp(-0.4, +0.6)

    for sound_wave in [sawtooth_wave, square_wave, fm_modulated_wave, am_modulated_wave]: # [am_modulated_wave]: 

        normal = sound_wave.normalize_rms(target_rms = 0.1)
        stereo = normal.to_stereo().haas_widen()
        sound_handle, channel_handle = service.play_sound(stereo)

        print(f"Expected duration={expected_duration}, reported duration={sound_handle.get_length()}")

        # Keep program alive long enough to hear it
        while channel_handle.get_busy():
            pygame.time.wait(1000)

        print("Channel no longer busy.")

    '''
    print("TEST TWO - KABOOM!")

    # 1 second of noise
    noise = service.white_noise(1.0)

    noise = service.clamp(noise, -0.2, 0.6)

    noise = service.normalize_rms(noise)

    # Shape it

    # Add a low sine thump
    t = numpy.arange(len(noise)) / service.frequency_sample_rate
    thump = numpy.sin(2*numpy.pi*60*t) * numpy.exp(-t/0.6)  # 60 Hz boom with 0.5s decay

    thump *= 2.0

    # Mix broadband
    blast = service.mix([noise, thump])

    blast = service.normalize_rms(blast)

    # Envelope shape (fast attack, 1s decay)
    blast = service.envelope(blast, attack=0.005, decay_fast=0.2, decay_slow=1.0)

    # Optional shimmer
    blast = service.phaser(blast, stages=6, lfo_hz=0.5, feedback=0.4, mix=0.8)

    blast = service.normalize_rms(blast)

    sound_handle, channel_handle = service.play_sound(blast)

    # Keep program alive long enough to hear it
    while channel_handle.get_busy():
        pygame.time.wait(1000)

    print("Channel no longer busy.")
    '''



