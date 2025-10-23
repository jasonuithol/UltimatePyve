import pygame
import numpy
from typing import Callable, Sequence, Union

from dark_libraries.logging import LoggerMixin

NDArrayInt8  = numpy.ndarray[tuple[int], numpy.dtype[numpy.int8]]
NDArrayUInt8 = numpy.ndarray[tuple[int], numpy.dtype[numpy.uint8]]
NDArrayInt16 = numpy.ndarray[tuple[int], numpy.dtype[numpy.int16]]
NDArrayInt32 = numpy.ndarray[tuple[int], numpy.dtype[numpy.int32]]

# For mixing/modulating, performing mathematical transforms on.
RawValueWaveArrayType = numpy.ndarray[numpy.float64]

# For multiple RawValueWaveArrayType in an array of unknown shape.
# Primarily used for mixing operations.  Could also be used for multi-channel effects applied prior to sampling.
RawValueMatrixArrayType = numpy.ndarray[numpy.float64]

# Sampled to the system's sample bit rate.
BitSampledWaveArrayType = Union[NDArrayInt8, NDArrayUInt8, NDArrayInt16, NDArrayInt32]

FADEOUT_MILLISECONDS = 1500

class SoundService(LoggerMixin):

    def init(self):
        pygame.mixer.init()
        self.sample_rate, self.sound_format, self.channels = pygame.mixer.get_init()
        self.log(f"Initialised pygame.mixer: sample_rate={self.sample_rate}, sound_format={self.sound_format}, channels={self.channels}")

        # Determine amplitude
        bits = abs(self.sound_format)
        signed = self.sound_format < 0
        if signed:
            self.amplitude = (2 ** (bits - 1)) - 1   # e.g. 32767 for 16‑bit signed
        else:
            self.amplitude = (2 ** bits) - 1         # e.g. 255 for 8‑bit unsigned

        self.log(f"Setting amplitude to {self.amplitude}")

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

        self.set_sfx_volume(0.05)
        self.set_soundtrack_volume(0.05)

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
    # SFX Generation and Playback
    #

    # Returns a single channel.
    def square_wave(self, hz: float, sec: float) -> RawValueWaveArrayType:
        input_wave = self.sine_wave(hz, sec)
        return numpy.sign(input_wave)

    def sine_wave(self, hz: float, sec: float) -> RawValueWaveArrayType:
        number_of_samples = int(self.sample_rate * sec)

        if not (0.0 <= hz < (self.sample_rate / 2)):
            return numpy.zeros((number_of_samples,), dtype=numpy.float64)

        time_axis: RawValueWaveArrayType = numpy.arange(number_of_samples, dtype=numpy.float64) / self.sample_rate
        return numpy.sin(2 * numpy.pi * hz * time_axis)

    def fm_modulated_wave(self, base_hz: float, sec: float, mod_freq: float, deviation_hz: float) -> RawValueWaveArrayType:
        n = int(self.sample_rate * sec)
        t = numpy.arange(n) / self.sample_rate
        # sine modulator
        mod = numpy.sin(2 * numpy.pi * mod_freq * t)
        # instantaneous phase with frequency deviation
        phase = 2 * numpy.pi * (base_hz * t + deviation_hz * mod.cumsum() / self.sample_rate)
        return numpy.sin(phase)

    def mix(self, input_waves: list[RawValueWaveArrayType]) -> RawValueWaveArrayType:
        # Stack into 2D array for vectorised mixing
        # Stacked is NOT a RawValueWaveArrayType because it's a different shape.
        # It is instead a RawValueMatrixArrayType, which contains many RawValueWaveArrayType's (abstractly)
        stacked: RawValueMatrixArrayType = numpy.vstack(input_waves).astype(numpy.float64)

        # Average across voices (prevents clipping)
        return stacked.mean(axis=0)

    def amplitude_modulate(self, carrier: RawValueWaveArrayType, modulator: RawValueWaveArrayType, depth: float = 1.0) -> RawValueWaveArrayType:
        envelope = 0.5 * (modulator + 1.0)
        return carrier * (1.0 - depth + depth * envelope)

    def from_frequency_duration_sequence(self, 
                                            input_sequence: Sequence[tuple[float, float]],
                                            wave_generator_func: Callable[[float, float], RawValueWaveArrayType]
                                         ) -> RawValueWaveArrayType:
        waves: list[RawValueWaveArrayType] = [wave_generator_func(hz, sec) for hz, sec in input_sequence]
        return numpy.concatenate(waves)

    def stereo_phase_widen(self, mono_wave: RawValueWaveArrayType,
                        ref_hz: float = 440.0,
                        phase_deg: float = 90.0) -> tuple[RawValueWaveArrayType, RawValueWaveArrayType]:
        # Fraction of a period as delay (seconds)
        delay_sec = (phase_deg / 360.0) / ref_hz
        delay_samples = delay_sec * self.sample_rate

        # Fractional delay with linear interpolation
        x = mono_wave.astype(numpy.float64)
        n = len(x)
        idx = numpy.arange(n, dtype=numpy.float64)
        shifted = numpy.interp(idx, idx - delay_samples, x, left=0.0, right=0.0)

        return x, shifted

    def haas_widen(self, input_wave: RawValueWaveArrayType, delay_seconds: float = 0.002) -> tuple[RawValueWaveArrayType, RawValueWaveArrayType]:
        delay_samples = int(delay_seconds * self.sample_rate)  # 2 ms
        left = input_wave
        right = numpy.concatenate([
            numpy.zeros(delay_samples, dtype=numpy.float64),
            input_wave[:-delay_samples]
        ])
        return left, right

    def to_bit_sampled_wave(self, input_wave: RawValueWaveArrayType) -> BitSampledWaveArrayType:
        return (input_wave * self.amplitude).astype(self.dtype)

    def play_sound(self, input_wave: RawValueWaveArrayType) -> tuple[pygame.mixer.Sound, pygame.mixer.Channel]:

        volume_adjusted:  RawValueWaveArrayType = (input_wave * self.sfx_volume)

        if self.channels == 2:
#            left, right = self.stereo_phase_widen(volume_adjusted, phase_deg = 90)
            left, right = self.haas_widen(volume_adjusted, delay_seconds = 0.020)
#            left, right = volume_adjusted, volume_adjusted
            channel_adjusted = numpy.column_stack((
                self.to_bit_sampled_wave(left), 
                self.to_bit_sampled_wave(right) 
            ))
        else:
             channel_adjusted = self.to_bit_sampled_wave(volume_adjusted)

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
        pygame.mixer.music.play(-1)

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

    pentatonic_sequence = [
        (440 * 2**(n / 12), 0.5)
        for n in [0, 2, 4, 7, 9, 12]
    ]
    expected_duration = sum(note[1] for note in pentatonic_sequence)

    square_wave = service.from_frequency_duration_sequence(pentatonic_sequence, service.square_wave)
    amplitude_modulation = service.sine_wave(20.0, expected_duration)
    am_modulated_wave = service.amplitude_modulate(carrier = square_wave, modulator = amplitude_modulation, depth = 1.0)

    fm_modulated_wave = service.from_frequency_duration_sequence(pentatonic_sequence, lambda hz, sec: service.fm_modulated_wave(hz, sec, mod_freq = 6.0, deviation_hz = 8.0))

    for sound_wave in [am_modulated_wave, fm_modulated_wave]: 

        sound_handle, channel_handle = service.play_sound(sound_wave)

        print(f"Expected duration={expected_duration}, reported duration={sound_handle.get_length()}")

        while channel_handle.get_busy():

        # Keep program alive long enough to hear it
            pygame.time.wait(1000)

        print("Channel no longer busy.")

