
from enum import Enum
from typing import Callable, Self, Sequence, Union
import numpy

NDArrayInt8  = numpy.ndarray[tuple[int], numpy.dtype[numpy.int8]]
NDArrayUInt8 = numpy.ndarray[tuple[int], numpy.dtype[numpy.uint8]]
NDArrayInt16 = numpy.ndarray[tuple[int], numpy.dtype[numpy.int16]]
NDArrayInt32 = numpy.ndarray[tuple[int], numpy.dtype[numpy.int32]]

# For mixing/modulating, performing mathematical transforms on.
RawValueWaveArrayType = numpy.ndarray[numpy.float64]

# Sampled to the system's sample bit rate.
BitSampledWaveArrayType = Union[NDArrayInt8, NDArrayUInt8, NDArrayInt16, NDArrayInt32]


WaveFunction = Callable[[float, float], 'DarkWave']
#StereoWaveFunction = Callable[[RawValueWaveArrayType, RawValueWaveArrayType], 'DarkWaveStereo']

class StereoChannel(Enum):
    Left = 0
    Right = 1


#
# Core functions
#
def fm_modulator(
    base_hz: float,
    modulator: RawValueWaveArrayType,
    deviation_hz: float,
    sample_rate: int
) -> RawValueWaveArrayType:
    """
    Frequency modulation kernel.

    Parameters
    ----------
    base_hz : float
        Carrier frequency in Hz (the 'center' pitch).
    modulator : np.ndarray
        Modulator samples in [-1, 1].
    deviation_hz : float
        Peak frequency deviation in Hz.
    sample_rate : int
        Sampling rate in Hz.

    Returns
    -------
    np.ndarray
        FM-modulated waveform (float64).
    """
    # instantaneous frequency = base + deviation * modulator
    inst_freq = base_hz + deviation_hz * modulator
    # integrate frequency to phase
    phase = 2 * numpy.pi * numpy.cumsum(inst_freq) / sample_rate
    return numpy.sin(phase, dtype=numpy.float64)

def am_modulator(
    carrier: RawValueWaveArrayType,
    modulator: RawValueWaveArrayType,
    depth: float = 1.0
) -> RawValueWaveArrayType:
    """
    Amplitude modulation kernel (vector-agnostic).

    Parameters
    ----------
    carrier : np.ndarray
        Carrier waveform. Shape (n,) for mono or (n, c) for multi-channel.
    modulator : np.ndarray
        Modulator waveform in [-1, 1]. Same shape as carrier.
    depth : float, optional
        Modulation depth in [0.0, 1.0].
        0.0 = dry (no modulation), 1.0 = full AM.

    Returns
    -------
    np.ndarray
        Amplitude-modulated waveform, same shape as carrier.
    """
#    carrier = numpy.asarray(carrier, dtype=numpy.float64)
#    modulator = numpy.asarray(modulator, dtype=numpy.float64)

    # Normalize modulator from [-1, 1] → [0, 1]
    envelope = 0.5 * (modulator + 1.0)

    # Apply depth control: dry + wet mix
    gain = (1.0 - depth) + depth * envelope

    return carrier * gain


#
# Stereo Post-processing
#

class DarkWaveStereo:
    
    def __init__(self, frequency_sample_rate: int, left: RawValueWaveArrayType, right: RawValueWaveArrayType):
        self.frequency_sample_rate = frequency_sample_rate
        self.left = left
        self.right = right

    def _dark_wave(self, wave_data: RawValueWaveArrayType):
        return DarkWave(self.frequency_sample_rate, wave_data)

    def _dark_wave_stereo(self, left: RawValueWaveArrayType, right: RawValueWaveArrayType) -> Self:
        return __class__(self.frequency_sample_rate, left, right)

    def stereo_phase_widen(self,
        channel:     StereoChannel = StereoChannel.Right,
        ref_hz:      float         = 440.0,
        phase_deg:   float         = 90.0,
    ) -> Self:

        # Convert phase offset to fractional delay in samples
        delay_sec = (phase_deg / 360.0) / ref_hz
        delay_samples = delay_sec * self.frequency_sample_rate

        # Fractional delay with linear interpolation
        number_of_freq_samples = len(left)
        idx = numpy.arange(number_of_freq_samples, dtype=numpy.float64)

        if channel == StereoChannel.Left:
            left  = numpy.interp(idx, idx - delay_samples, self.left.astype (self.left.dtype ), left=0.0, right=0.0)
        elif channel == StereoChannel.Right:
            right = numpy.interp(idx, idx - delay_samples, self.right.astype(self.right.dtype), left=0.0, right=0.0)

        return self._dark_wave_stereo(left, right)

    def haas_widen(self, 
        channel :      StereoChannel = StereoChannel.Right,
        delay_seconds: float         = 0.002

    ) -> Self:
        
        left, right = self.left, self.right
        delay_samples = int(delay_seconds * self.frequency_sample_rate)

        if channel == StereoChannel.Left:
            left = numpy.concatenate([
                numpy.zeros(delay_samples, dtype=left.dtype),
                left[:-delay_samples]
            ])
        elif channel == StereoChannel.Right:
            right = numpy.concatenate([
                numpy.zeros(delay_samples, dtype=right.dtype),
                right[:-delay_samples]
            ])
        return self._dark_wave_stereo(left, right)

    def stereo_balance_modulator(
        self,
        lfo_hz: float = 0.5
    ) -> Self:
        
        left, right = self.left, self.right
        n_samples = len(left)
        if len(right) != n_samples:
            raise ValueError("Left and right channels must have the same length")

        t = numpy.arange(n_samples, dtype=numpy.float64) / self.frequency_sample_rate
        lfo = 0.5 * (1.0 + numpy.sin(2.0 * numpy.pi * lfo_hz * t))  # 0..1

        # Scale left and right inversely
        left_mod  = left.astype(numpy.float64)  * lfo
        right_mod = right.astype(numpy.float64) * (1.0 - lfo)

        return self._dark_wave_stereo(left_mod, right_mod)

    def stereo_mid_side(
        self,
        side_gain: float = 1.5
    ) -> Self:
        left, right = self.left, self.right
        if len(left) != len(right):
            raise ValueError("Left and right channels must have the same length")

        left = left.astype(numpy.float64)
        right = right.astype(numpy.float64)

        mid = 0.5 * (left + right)
        side = 0.5 * (left - right)

        side *= side_gain

        new_left = mid + side
        new_right = mid - side

        return self._dark_wave_stereo(new_left, new_right)

    def stereo_phaser(
        self,
        stages: int = 4,
        lfo_hz: float = 0.5,
        min_fc: float = 300.0,
        max_fc: float = 1500.0,
        feedback: float = 0.0,
        mix: float = 0.7,
        phase_offset: float = numpy.pi
    ) -> Self:
        
        left, right = self._dark_wave(self.left), self._dark_wave(self.right)

        # Left channel: normal phaser
        left_out  =  left.phaser(stages, lfo_hz, min_fc, max_fc, feedback, mix, lfo_phase = 0.0)
        right_out = right.phaser(stages, lfo_hz, min_fc, max_fc, feedback, mix, lfo_phase = phase_offset)

        return self._dark_wave_stereo(left_out.wave_data, right_out.wave_data)

class DarkWave:

    def __init__(self, frequency_sample_rate: int, wave_data: numpy.ndarray[numpy.float64]):
        self.frequency_sample_rate = frequency_sample_rate
        self.wave_data = wave_data

    def _dark_wave(self, wave_data: numpy.ndarray[numpy.float64]) -> Self:
        return __class__(self.frequency_sample_rate, wave_data)

    #
    # Mixers/modulators/filters
    #

    def clamp(self, min: float, max: float) -> Self:
        return self._dark_wave(numpy.clip(self.wave_data, min, max))

    def mix(self, other: Self) -> Self:
        stacked = numpy.vstack([self.wave_data, other.wave_data])
        return self._dark_wave(stacked.sum(axis=0))

    def amplitude_modulate(self, modulator: Self, depth: float = 1.0) -> Self:
        am_wave = am_modulator(self.wave_data, modulator.wave_data, depth)
        return self._dark_wave(am_wave)

    def frequency_modulate(self, modulator: Self, base_hz: float, deviation_hz: float) -> Self:
        fm_wave = fm_modulator(base_hz, modulator.wave_data, deviation_hz, self.frequency_sample_rate)
        return self._dark_wave(fm_wave)

    def _one_pole_allpass(self, x: RawValueWaveArrayType, a: float) -> Self:
        # y[n] = -a*x[n] + x[n-1] + a*y[n-1]
        y = numpy.zeros_like(x, dtype=numpy.float64)
        xn1 = 0.0
        yn1 = 0.0
        for n in range(len(x)):
            y[n] = -a * x[n] + xn1 + a * yn1
            xn1 = x[n]
            yn1 = y[n]
        return y

    def _a_from_fc(self, fc: float) -> float:
        # Bilinear transform mapping (Tustin). fc normalized to Hz.
        # a = (1 - tan(pi*fc/fs)) / (1 + tan(pi*fc/fs))
        t = numpy.tan(numpy.pi * fc / self.frequency_sample_rate)
        return (1.0 - t) / (1.0 + t)

    def phaser(self,
            stages: int = 4,
            lfo_hz: float = 0.3,
            min_fc: float = 300.0,
            max_fc: float = 1500.0,
            feedback: float = 0.0,
            mix: float = 0.7,
            lfo_phase: float = 0.0   # NEW, in radians
            ) -> Self:
        """
        Simple multi‑stage phaser:
        - stages: number of all‑pass cascades (2–8 typical)
        - lfo_hz: sweep rate
        - min_fc/max_fc: sweep range (Hz)
        - feedback: 0.0–0.7 to intensify notches
        - mix: wet/dry mix
        """
        number_frequency_samples = len(self.wave_data)
        time_axis = numpy.arange(number_frequency_samples) / self.frequency_sample_rate
        # LFO in [0,1]
        lfo = 0.5 * (1.0 + numpy.sin(2 * numpy.pi * lfo_hz * time_axis + lfo_phase))
        # Sweep cutoff per sample
        fc = min_fc + (max_fc - min_fc) * lfo
        # Precompute a(t) per sample
        a_t = (1.0 - numpy.tan(numpy.pi * fc / self.frequency_sample_rate)) / (1.0 + numpy.tan(numpy.pi * fc / self.frequency_sample_rate))

        y = self.wave_data.copy()
        fb = 0.0
        for _ in range(stages):
            # Per-sample varying a: apply as time‑varying filter
            # Loop for clarity; vectorized versions exist but are less readable
            out = numpy.zeros_like(y)
            xn1 = 0.0
            yn1 = 0.0
            for i in range(number_frequency_samples):
                xi = y[i] + feedback * fb
                ai = a_t[i]
                yi = -ai * xi + xn1 + ai * yn1
                out[i] = yi
                xn1 = xi
                yn1 = yi
            fb = out[-1]
            y = out

        # Wet/dry mix
        return self._dark_wave((1.0 - mix) * self.wave_data + mix * y)
    
    def envelope(self, attack: float, decay_fast=0.2, decay_slow=1.0) -> Self:
        n = len(self.wave_data)
        t = numpy.arange(n) / self.frequency_sample_rate
        env = numpy.exp(-t/decay_slow)
        env *= numpy.exp(-t/decay_fast)  # fast initial drop
        env[:int(attack*self.frequency_sample_rate)] = numpy.linspace(0, 1, int(attack*self.frequency_sample_rate))
        return self._dark_wave(self.wave_data * env)

    def normalize_rms(self, target_rms: float = 0.1) -> Self:
        rms = numpy.sqrt(numpy.mean(self.wave_data**2))
        if rms < 1e-9:
            return self  # avoid divide-by-zero
        return self._dark_wave(self.wave_data * (target_rms / rms))
    
    def to_stereo(self) -> DarkWaveStereo:
        return DarkWaveStereo(self.frequency_sample_rate, left = self.wave_data, right = self.wave_data)
    
class DarkWaveGenerator:

    def __init__(self, frequency_sample_rate: int):
        self.frequency_sample_rate = frequency_sample_rate       

    def _dark_wave(self, wave_data: numpy.ndarray[numpy.float64]) -> DarkWave:
        return DarkWave(self.frequency_sample_rate, wave_data)

    def _dark_wave_sequencer(self, wave_function: WaveFunction) -> 'DarkWaveSequencer':
        return DarkWaveSequencer(self.frequency_sample_rate, wave_function)

    def sawtooth_wave(self) -> 'DarkWaveSequencer':

        def _wave_function(hz: float, sec: float):
            n_samples = int(self.frequency_sample_rate * sec)

            if not (0.0 <= hz < (self.frequency_sample_rate / 2)):
                return numpy.zeros((n_samples,), dtype=numpy.float64)

            t = numpy.arange(n_samples, dtype=numpy.float64) / self.frequency_sample_rate
            # Basic sawtooth: fractional part of (hz * t), scaled to [-1, 1]
            return self._dark_wave(2.0 * (hz * t % 1.0) - 1.0)
        
        return self._dark_wave_sequencer(_wave_function)

    def square_wave(self) -> 'DarkWaveSequencer':

        def _wave_function(hz: float, sec: float):
            input_wave = self.sine_wave().sequence([(hz, sec)])
            return self._dark_wave(numpy.sign(input_wave.wave_data))
        
        return self._dark_wave_sequencer(_wave_function)

    def sine_wave(self) -> 'DarkWaveSequencer':

        def _wave_function(hz: float, sec: float):

            number_of_samples = int(self.frequency_sample_rate * sec)

            assert 0.0 <= hz < (self.frequency_sample_rate / 2), f"hz must be between 0 and {self.frequency_sample_rate / 2}"

            time_axis: RawValueWaveArrayType = numpy.arange(number_of_samples, dtype=numpy.float64) / self.frequency_sample_rate
            return self._dark_wave(numpy.sin(2 * numpy.pi * hz * time_axis))
        return self._dark_wave_sequencer(_wave_function)

    def fm_modulated_wave(self, mod_freq: float, deviation_hz: float) -> 'DarkWaveSequencer':

        def _wave_function(base_hz: float, sec: float):
            n = int(self.frequency_sample_rate * sec)
            t = numpy.arange(n) / self.frequency_sample_rate

            modulator = numpy.sin(2 * numpy.pi * mod_freq * t)
            fm_wave = fm_modulator(base_hz, modulator, deviation_hz, self.frequency_sample_rate)
            return self._dark_wave(fm_wave)

        return self._dark_wave_sequencer(_wave_function)

    def am_modulated_wave(self, mod_freq: float, depth: float = 1.0) -> 'DarkWaveSequencer':
        """
        Construct an amplitude-modulated (tremolo) wave generator.

        Parameters
        ----------
        mod_freq : float
            Frequency of the modulation oscillator in Hz.
        depth : float
            Modulation depth in [0.0, 1.0].
        """
        def _wave_function(base_hz: float, sec: float):
            n = int(self.frequency_sample_rate * sec)
            t = numpy.arange(n) / self.frequency_sample_rate

            # Carrier: sine at base_hz
            carrier = numpy.sin(2 * numpy.pi * base_hz * t)

            # Modulator: sine in [-1, 1] at mod_freq
            modulator = numpy.sin(2 * numpy.pi * mod_freq * t)

            # Apply AM kernel
            am_wave = am_modulator(carrier, modulator, depth)

            return self._dark_wave(am_wave)

        return self._dark_wave_sequencer(_wave_function)

    def white_noise(self, sec: float) -> DarkWave:
        n_samples = int(self.frequency_sample_rate * sec)
        return self._dark_wave(numpy.random.uniform(-1.0, 1.0, n_samples).astype(numpy.float64))

class DarkWaveSequencer:

    def __init__(self, frequency_sample_rate: int, wave_function: WaveFunction):
        self.frequency_sample_rate = frequency_sample_rate
        self.wave_function   = wave_function

    def sequence(self, input_sequence: Sequence[tuple[float, float]]) -> DarkWave:
        waves: list[RawValueWaveArrayType] = [self.wave_function(hz, sec).wave_data for hz, sec in input_sequence]
        return DarkWave(self.frequency_sample_rate, numpy.concatenate(waves))
    
