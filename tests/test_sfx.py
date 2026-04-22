import numpy as np
import pygame
import pytest


SAMPLE_RATE = 44100
DURATION_S = 0.5
FREQ_HZ = 440


@pytest.fixture(scope="module")
def mixer():
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
    yield
    pygame.mixer.quit()


def _sine_stereo():
    t = np.linspace(0, DURATION_S, int(SAMPLE_RATE * DURATION_S), endpoint=False)
    wave = np.sin(2 * np.pi * FREQ_HZ * t) * 32767
    return np.column_stack((wave, wave)).astype(np.int16)


def test_sine_array_shape_and_dtype():
    stereo = _sine_stereo()
    assert stereo.shape == (int(SAMPLE_RATE * DURATION_S), 2)
    assert stereo.dtype == np.int16
    assert stereo.max() <= 32767 and stereo.min() >= -32768


def test_sine_dominant_frequency():
    stereo = _sine_stereo()
    mono = stereo[:, 0].astype(np.float64)
    spectrum = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), d=1 / SAMPLE_RATE)
    peak_hz = freqs[int(np.argmax(spectrum))]
    assert peak_hz == pytest.approx(FREQ_HZ, abs=2.0)


def test_make_sound_round_trip(mixer):
    stereo = _sine_stereo()
    sound = pygame.sndarray.make_sound(stereo)
    assert sound is not None
    assert sound.get_length() == pytest.approx(DURATION_S, abs=0.05)
