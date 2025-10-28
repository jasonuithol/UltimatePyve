
from enum import Enum
from typing import NamedTuple, Protocol, Self, Sequence

import numpy as np
import numpy.typing as npt

# For generating/mixing/modulating, performing mathematical transforms on.
DarkWaveFloatArray = npt.NDArray[np.float64]

frequency_sample_rate: int = None

# get this from the system's frequency_sample_rate e.g. pygame.mixer.init()
def set_frequency_sample_rate(value: int):
    global frequency_sample_rate
    frequency_sample_rate = value
    print(f"(dark_wave) Set module level frequency_sample_rate={frequency_sample_rate}")

#
# Core functions
#
def fm_modulator(
    base_hz: float,                  # Carrier frequency in Hz (the 'center' pitch).
    modulator: DarkWaveFloatArray,   # Modulator samples in [-1.0, 1.0].
    deviation_hz: float,             # Peak frequency deviation in Hz.

) -> DarkWaveFloatArray:             # FM-modulated waveform (float64).

    # instantaneous frequency = base + deviation * modulator
    inst_freq = base_hz + deviation_hz * modulator
    # integrate frequency to phase
    phase = 2 * np.pi * np.cumsum(inst_freq) / frequency_sample_rate
    return np.sin(phase, dtype=np.float64)

def am_modulator(
    carrier: DarkWaveFloatArray,     # Carrier waveform. Shape (n,) for mono or (n, c) for multi-channel.
    modulator: DarkWaveFloatArray,   # Modulator waveform in [-1, 1]. Same shape as carrier.
    depth: float = 1.0               # Modulation depth in [0.0, 1.0]. 0.0 = dry (no modulation), 1.0 = full AM.

) -> DarkWaveFloatArray:             # Amplitude-modulated waveform, same shape as carrier.

    # Normalize modulator from [-1, 1] → [0, 1]
    envelope = 0.5 * (modulator + 1.0)

    # Apply depth control: dry + wet mix
    gain = (1.0 - depth) + depth * envelope

    return carrier * gain


HarmonicSpec = tuple[int, float, float]  # (multiplier, amplitude, phase)

class HarmonicSpec(NamedTuple):
    multiplier: int
    amplitude:  float
    phase:      float

def harmonic_generator(
    base_hz:   float,                  # the fundamental frequency that the other harmonics are based on.
    harmonics: Sequence[HarmonicSpec], # a list of (multiplier: int, amplitude: float, phase: float)
    duration:  float                  # in seconds

) -> DarkWaveFloatArray:
    
    # build raw wave
    t = np.linspace(0, duration, int(frequency_sample_rate * duration), endpoint=False, dtype=np.float64)
    signal = np.zeros_like(t)
    for mult, amp, phase in harmonics:
        signal += amp * np.sin(2 * np.pi * base_hz * mult * t + phase)

    # normalize
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal /= max_val
    return signal


class PowerRule(Enum):
    Additive       = 0   # raw sum, output power grows with N inputs.

    Mean           = 1   # arithmetic average of N input signals;
                         # equals one input if all are identical,
                         # otherwise output RMS is lower than the average input power.

    RootMeanSquare = 2   # RMS-consistent, preserves perceived loudness.

    Peak           = 3   # normalize to maximum absolute amplitude; ensures no clipping,
                         # but RMS power varies (up or down) with input waveform shapes.

Unity = PowerRule.Additive # Emphasise the raw arithmetic involved.  It's either a straight copy (if splitting) or straight addition (if mixing)

GainMatrix   = npt.NDArray[np.float64]
SignalMatrix = npt.NDArray[np.float64]

# Compute an (n_out x n_in) gain matrix according to the PowerRule.
def create_gain_matrix(
    n_in:  int,      # number of input  waves to use this matrix for
    n_out: int,      # number of output waves to use this matrix for
    pan:   float,    # -1.0 = left, 0.0 = center, +1.0 = right (only meaningful for 1→2).
    rule:  PowerRule # how to maintain/transform/ignore wave power.

) -> GainMatrix:

    if n_in == 1 and n_out == 2:
        # mono → stereo panning
        if rule == PowerRule.Additive or rule == PowerRule.Mean:
            t = (pan + 1.0) / 2.0
            L, R = 1.0 - t, t
            if rule == PowerRule.Mean:
                L, R = L/2.0, R/2.0
        elif rule == PowerRule.RootMeanSquare:
            theta = (pan + 1.0) * np.pi / 4.0
            L, R = np.cos(theta), np.sin(theta)
        elif rule == PowerRule.Peak:
            t = (pan + 1.0) / 2.0
            L, R = 1.0 - t, t
            norm = max(abs(L), abs(R))
            if norm > 0:
                L, R = L/norm, R/norm
        else:
            raise ValueError(rule)
        return np.eye(n_out, n_in, dtype=np.float64)

    elif n_in > 1 and n_out == 1:
        # downmix N → mono
        if rule == PowerRule.Additive:
            gains = np.ones((1, n_in))
        elif rule == PowerRule.Mean:
            gains = np.ones((1, n_in)) / n_in
        elif rule == PowerRule.RootMeanSquare:
            gains = np.ones((1, n_in)) / np.sqrt(n_in)
        elif rule == PowerRule.Peak:
            gains = np.ones((1, n_in)) / np.max(np.abs(np.ones(n_in)))
        else:
            raise ValueError(rule)
        return gains

    elif n_in == n_out:
        # passthrough (stereo→stereo, etc.)
        return np.eye(n_in)

    else:
        raise NotImplementedError(f"{n_in}→{n_out} not defined for {rule}")

# Apply a channel gain matrix to a multichannel signal.
def apply_gain_matrix(
        gains:  GainMatrix,   # Shape (n_out, n_in). Each row defines how input channels are mixed into one output channel.
        signal: SignalMatrix  # Shape (n_in, n_samples). Multichannel input signal.
    ) -> SignalMatrix:        # Shape (n_out, n_samples). Output signal after applying the gain matrix.

    assert  gains.ndim == 2, f"gains  must be 2D, got shape {gains.shape}"
    assert signal.ndim == 2, f"signal must be 2D, got shape {signal.shape}"

    _, n_in = gains.shape
    in_channels, _ = signal.shape

    assert in_channels == n_in, f"gain matrix expects {n_in} input channels, got {in_channels}"

    # matrix multiply: (n_out × n_in) @ (n_in × n_samples) → (n_out × n_samples)
    return gains @ signal


#
# Stereo Post-processing
#

class StereoChannel(Enum):
    Left = 0
    Right = 1

class DarkWaveStereo:
    
    def __init__(self, left: DarkWaveFloatArray, right: DarkWaveFloatArray):
        self.left = left
        self.right = right

    def _dark_wave(self, wave_data: DarkWaveFloatArray):
        return DarkWave(wave_data)

    def _dark_wave_stereo(self, left: DarkWaveFloatArray, right: DarkWaveFloatArray) -> Self:
        return __class__(left, right)

    def stereo_phase_widen(self,
        channel:     StereoChannel = StereoChannel.Right,
        ref_hz:      float         = 440.0,
        phase_deg:   float         = 90.0,
    ) -> Self:

        # Convert phase offset to fractional delay in samples
        delay_sec = (phase_deg / 360.0) / ref_hz
        delay_samples = delay_sec * frequency_sample_rate

        # Fractional delay with linear interpolation
        number_of_freq_samples = len(left)
        idx = np.arange(number_of_freq_samples, dtype=np.float64)

        if channel == StereoChannel.Left:
            left  = np.interp(idx, idx - delay_samples, self.left.astype (self.left.dtype ), left=0.0, right=0.0)
        elif channel == StereoChannel.Right:
            right = np.interp(idx, idx - delay_samples, self.right.astype(self.right.dtype), left=0.0, right=0.0)

        return self._dark_wave_stereo(left, right)

    def haas_widen(self, 
        channel :      StereoChannel = StereoChannel.Right,
        delay_seconds: float         = 0.002

    ) -> Self:
        
        left, right = self.left, self.right
        delay_samples = int(delay_seconds * frequency_sample_rate)

        if channel == StereoChannel.Left:
            left = np.concatenate([
                np.zeros(delay_samples, dtype=left.dtype),
                left[:-delay_samples]
            ])
        elif channel == StereoChannel.Right:
            right = np.concatenate([
                np.zeros(delay_samples, dtype=right.dtype),
                right[:-delay_samples]
            ])
        return self._dark_wave_stereo(left, right)

    # pan left and right according to a modulating signal (pan-curve)
    def modulate_pan(
        self,

        # array of float: Shape (n_samples,). Values in [-1.0, +1.0]. -1.0 = hard left, 0.0 = center, +1.0 = hard right.
        pan_curve: DarkWaveFloatArray,                 
       
        rule: PowerRule = PowerRule.RootMeanSquare
    ) -> Self:

        left, right = self.left, self.right

        # Vectorized gain computation
        if rule in (PowerRule.Additive, PowerRule.Mean):
            t = (pan_curve + 1.0) / 2.0
            L, R = 1.0 - t, t
            if rule == PowerRule.Mean:
                L, R = L / 2.0, R / 2.0
        elif rule == PowerRule.RootMeanSquare:
            theta = (pan_curve + 1.0) * np.pi / 4.0
            L, R = np.cos(theta), np.sin(theta)
        elif rule == PowerRule.Peak:
            t = (pan_curve + 1.0) / 2.0
            L, R = 1.0 - t, t
            norm = np.maximum(np.abs(L), np.abs(R))
            norm[norm == 0] = 1.0
            L, R = L / norm, R / norm
        else:
            assert False, f"Not implemented for power rule {rule.name}"

        left_mod  = left.astype(np.float64)  * L
        right_mod = right.astype(np.float64) * R

        return self._dark_wave_stereo(left_mod, right_mod)

    def stereo_mid_side(
        self,
        side_gain: float = 1.5
    ) -> Self:
        left, right = self.left, self.right
        if len(left) != len(right):
            raise ValueError("Left and right channels must have the same length")

        left = left.astype(np.float64)
        right = right.astype(np.float64)

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
        phase_offset: float = np.pi
    ) -> Self:
        
        left, right = self._dark_wave(self.left), self._dark_wave(self.right)

        # Left channel: normal phaser
        left_out  =  left.phaser(stages, lfo_hz, min_fc, max_fc, feedback, mix, lfo_phase = 0.0)
        right_out = right.phaser(stages, lfo_hz, min_fc, max_fc, feedback, mix, lfo_phase = phase_offset)

        return self._dark_wave_stereo(left_out.wave_data, right_out.wave_data)

    def pan(
            self, 
            pan:  float, # -1.0 = hard left, 0.0 = center, +1.0 = hard right.
            rule: PowerRule = PowerRule.RootMeanSquare

        ) -> Self:
        
        stereo = np.vstack([self.left, self.right])  # (2, n_samples)
        gains = create_gain_matrix(n_in=2, n_out=2, pan=pan, rule=rule)
        panned = apply_gain_matrix(gains, stereo)
        return self._dark_wave_stereo(left=panned[0], right=panned[1])

class DarkWave:

    def __init__(self, wave_data: np.ndarray[np.float64]):
        self.wave_data = wave_data

    def _dark_wave(self, wave_data: np.ndarray[np.float64]) -> Self:
        return __class__(wave_data)
    
    def __len__(self) -> int:
        return self.wave_data.__len__()

    #
    # Mixers/modulators/filters
    #

    def clamp(self, min: float, max: float) -> Self:
        return self._dark_wave(np.clip(self.wave_data, min, max))

    def mix(self, other: Self, rule: PowerRule = PowerRule.Additive) -> Self:
        assert isinstance(other, __class__), f"Expected {__class__.__name__}, got {other.__class__.__name__}"

        # stack into shape (n_in, n_samples)
        stacked = np.vstack([self.wave_data, other.wave_data])  # (2, n_samples)

        # build a 1×2 gain matrix according to the rule
        gains = create_gain_matrix(n_in=2, n_out=1, pan=0.0, rule=rule)

        # apply it: (1×2) @ (2×n_samples) → (1×n_samples)
        mixed = apply_gain_matrix(gains, stacked)

        return self._dark_wave(mixed[0])  # flatten back to 1D

    def amplitude_modulate(self, modulator_wave: DarkWaveFloatArray, depth: float = 1.0) -> Self:
        am_wave = am_modulator(self.wave_data, modulator_wave, depth)
        return self._dark_wave(am_wave)

    def frequency_modulate(self, modulator_wave: DarkWaveFloatArray, base_hz: float, deviation_hz: float) -> Self:
        fm_wave = fm_modulator(base_hz, modulator_wave, deviation_hz)
        return self._dark_wave(fm_wave)

    def _one_pole_allpass(self, x: DarkWaveFloatArray, a: float) -> Self:
        # y[n] = -a*x[n] + x[n-1] + a*y[n-1]
        y = np.zeros_like(x, dtype=np.float64)
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
        t = np.tan(np.pi * fc / frequency_sample_rate)
        return (1.0 - t) / (1.0 + t)

    def phaser(self,
            stages:    int   = 4,      # number of all‑pass cascades (2–8 typical)
            lfo_hz:    float = 0.3,    # sweep rate
            min_fc:    float = 300.0,  # sweep range (Hz)
            max_fc:    float = 1500.0, # sweep range (Hz)
            feedback:  float = 0.0,    # 0.0–0.7 to intensify notches
            mix:       float = 0.7,    # wet/dry mix
            lfo_phase: float = 0.0     # phase offset in radians

    ) -> Self:
        number_frequency_samples = len(self.wave_data)
        time_axis = np.arange(number_frequency_samples) / frequency_sample_rate
        # LFO in [0,1]
        lfo = 0.5 * (1.0 + np.sin(2 * np.pi * lfo_hz * time_axis + lfo_phase))
        # Sweep cutoff per sample
        fc = min_fc + (max_fc - min_fc) * lfo
        # Precompute a(t) per sample
        a_t = (1.0 - np.tan(np.pi * fc / frequency_sample_rate)) / (1.0 + np.tan(np.pi * fc / frequency_sample_rate))

        y = self.wave_data.copy()
        fb = 0.0
        for _ in range(stages):
            # Per-sample varying a: apply as time‑varying filter
            # Loop for clarity; vectorized versions exist but are less readable
            out = np.zeros_like(y)
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
        t = np.arange(n) / frequency_sample_rate
        env = np.exp(-t/decay_slow)
        env *= np.exp(-t/decay_fast)  # fast initial drop
        env[:int(attack * frequency_sample_rate)] = np.linspace(0, 1, int(attack * frequency_sample_rate))
        return self._dark_wave(self.wave_data * env)

    def normalize_rms(self, target_rms: float = 0.1) -> Self:
        rms = np.sqrt(np.mean(self.wave_data**2))
        if rms < 1e-9:
            return self  # avoid divide-by-zero
        return self._dark_wave(self.wave_data * (target_rms / rms))
        
    """
    Convert mono DarkWave(s) into stereo.

    Modes:
    - No args: split `self` into stereo using a pan law (1→2).
    - left=...: merge `left` and `self` (as right) into stereo (2→2).
    - right=...: merge `self` (as left) and `right` into stereo (2→2).

    Supplying both left and right is not allowed.
    """
    def to_stereo(
        self,
        *,
        left:  Self | None = None,
        right: Self | None = None,
        rule: PowerRule = PowerRule.RootMeanSquare

    ) -> DarkWaveStereo:

        assert left is None or right is None, "Supply only left or right, or neither. Not both."

        if left is not None:
            stacked = np.vstack([left.wave_data, self.wave_data])  # (2, n_samples)
            gains = create_gain_matrix(n_in=2, n_out=2, pan=0.0, rule=rule)
            stereo = apply_gain_matrix(gains, stacked)
            return DarkWaveStereo(left=stereo[0], right=stereo[1])

        if right is not None:
            stacked = np.vstack([self.wave_data, right.wave_data])  # (2, n_samples)
            gains = create_gain_matrix(n_in=2, n_out=2, pan=0.0, rule=rule)
            stereo = apply_gain_matrix(gains, stacked)
            return DarkWaveStereo(left=stereo[0], right=stereo[1])

        # Default: split self into stereo with pan law
        mono = np.atleast_2d(self.wave_data)  # (1, n_samples)
        gains = create_gain_matrix(n_in=1, n_out=2, pan=0.0, rule=rule)
        stereo = apply_gain_matrix(gains, mono)
        return DarkWaveStereo(left=stereo[0], right=stereo[1])

class DarkNote(tuple):

    __slots__ = ()

    def __new__(cls, hz: float, sec: float):

        if isinstance(hz,  int): hz  = float(hz)
        if isinstance(sec, int): sec = float(sec)

        assert isinstance(hz,  float),  f"hz expects a float, got {type(hz).__name__}"
        assert isinstance(sec, float), f"sec expects a float, got {type(sec).__name__}"

        assert 0.0 <= hz < frequency_sample_rate / 2, f"expected 0.0 <= hz < {frequency_sample_rate / 2}, got hz={hz}"
        assert 0.0 < sec,                             f"expected sec > 0.0, got sec={sec}"

        return super().__new__(cls, (hz, sec))

    @property
    def hz(self) -> float:
        return self[0]

    @property
    def sec(self) -> float:
        return self[1]

#WaveFunction = Callable[[float, float], 'DarkWave']
class WaveFunction(Protocol):
    def __call__(self, note: DarkNote) -> DarkWave: 
        ...

class DarkWaveGenerator:

    def _dark_wave(self, wave_data: np.ndarray[np.float64]) -> DarkWave:
        return DarkWave(wave_data)

    def _dark_wave_sequencer(self, wave_function: WaveFunction) -> 'DarkWaveSequencer':
        return DarkWaveSequencer(wave_function)

    def sawtooth_wave(self, geometry: float = 0.0) -> 'DarkWaveSequencer':
        """
        Generate a skewed sawtooth/triangle wave.

        Parameters
        ----------
        geometry : float in [-1, 1]
            -1.0 = right-angled sawtooth (instant rise, long fall)
            0.0 = isosceles triangle
            +1.0 = right-angled sawtooth (long rise, instant fall)
        """

        def _wave_function(note: DarkNote):
            assert 0.0 <= note.hz < (frequency_sample_rate / 2), \
                f"hz must be between 0 and {frequency_sample_rate / 2}"
            n_samples = int(frequency_sample_rate * note.sec)
            t = np.arange(n_samples, dtype=np.float64) / frequency_sample_rate

            # Phase in [0,1)
            phase = (note.hz * t) % 1.0

            # Map geometry [-1,1] -> duty cycle [0,1]
            d = (geometry + 1.0) / 2.0

            if d == 0.0:
                # Degenerate: instant rise, long fall
                wave = 1.0 - phase
            elif d == 1.0:
                # Degenerate: long rise, instant fall
                wave = phase
            else:
                wave = np.empty_like(phase)
                rise = phase < d
                wave[rise] = phase[rise] / d
                wave[~rise] = 1.0 - (phase[~rise] - d) / (1.0 - d)

            # Scale to [-1, 1]
            return self._dark_wave(2.0 * wave - 1.0)

        return self._dark_wave_sequencer(_wave_function)

    def square_wave(self) -> 'DarkWaveSequencer':

        def _wave_function(note: DarkNote):
            assert 0.0 <= note.hz < (frequency_sample_rate / 2), f"hz must be between 0 and {frequency_sample_rate / 2}"
            input_wave = self.sine_wave().sequence([note])
            return self._dark_wave(np.sign(input_wave.wave_data))
        
        return self._dark_wave_sequencer(_wave_function)

    def sine_wave(self, phase_offset: float = 0.0) -> 'DarkWaveSequencer':

        def _wave_function(note: DarkNote):
            assert 0.0 <= note.hz < (frequency_sample_rate / 2), f"hz must be between 0 and {frequency_sample_rate / 2}"

            number_of_samples = int(frequency_sample_rate * note.sec)
            time_axis: DarkWaveFloatArray = np.arange(number_of_samples, dtype=np.float64) / frequency_sample_rate
            return self._dark_wave(np.sin(2 * np.pi * note.hz * time_axis + phase_offset))
        return self._dark_wave_sequencer(_wave_function)

    def fm_modulated_wave(self, mod_freq: float, deviation_hz: float) -> 'DarkWaveSequencer':

        def _wave_function(note: DarkNote):
            n = int(frequency_sample_rate * note.sec)
            t = np.arange(n) / frequency_sample_rate

            modulator = np.sin(2 * np.pi * mod_freq * t)
            fm_wave = fm_modulator(note.hz, modulator, deviation_hz)
            return self._dark_wave(fm_wave)

        return self._dark_wave_sequencer(_wave_function)

    def am_modulated_wave(
        self, 
        mod_freq: float,        # Frequency of the modulation oscillator in Hz.
        depth:    float = 1.0   # Modulation depth in [0.0, 1.0].

    ) -> 'DarkWaveSequencer':
        
        def _wave_function(note: DarkNote):
            n = int(frequency_sample_rate * note.sec)
            t = np.arange(n) / frequency_sample_rate

            # Carrier: sine at base_hz
            carrier = np.sin(2 * np.pi * note.hz * t)

            # Modulator: sine in [-1, 1] at mod_freq
            modulator = np.sin(2 * np.pi * mod_freq * t)

            # Apply AM kernel
            am_wave = am_modulator(carrier, modulator, depth)

            return self._dark_wave(am_wave)

        return self._dark_wave_sequencer(_wave_function)

    def white_noise(self, hz: float, sec: float) -> DarkWave:
        """
        Generate sample-and-hold white noise.

        Parameters
        ----------
        hz : float
            Update rate of the noise (new random value per second).
        sec : float
            Duration in seconds.

        Returns
        -------
        DarkWave
            Noise signal of length sec * sample_rate.
        """
        assert hz > 0, "hz must be positive"
        n_samples = int(frequency_sample_rate * sec)

        # Number of samples per hold interval (may be fractional)
        samples_per_step = frequency_sample_rate / hz

        # Number of random values needed
        n_randoms = int(np.ceil(n_samples / samples_per_step))

        # Generate random values
        randoms = np.random.uniform(-1.0, 1.0, n_randoms)

        # Repeat each random value for the right number of samples
        samples = np.repeat(randoms, np.ceil(samples_per_step).astype(int))

        # Truncate to exact length
        samples = samples[:n_samples]

        return self._dark_wave(samples.astype(np.float64))


class DarkWaveSequencer:

    def __init__(self, wave_function: WaveFunction):
        self.wave_function = wave_function

    def sequence(self, input_sequence: Sequence[DarkNote]) -> DarkWave:
        waves: list[DarkWaveFloatArray] = [self.wave_function(note).wave_data for note in input_sequence]
        return DarkWave(np.concatenate(waves))
    
