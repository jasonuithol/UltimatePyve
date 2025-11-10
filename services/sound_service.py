from typing import Protocol
import pygame

from dark_libraries.dark_wave import DarkWave, DarkWaveGenerator, DarkWaveStereo
from service_implementations.sound_service_implementation import PlaySfxHandle

class SoundService(Protocol):

    # Main thread only
    def init(self): ...

    #
    # Volume Control
    #

    # Main thread only
    def set_soundtrack_volume(self, value: float) -> None: ...

    # Worker thread friendly
    def get_soundtrack_volume(self) -> float: ...
    def set_sfx_volume(self, value: float) -> None: ...
    def get_sfx_volume(self) -> float: ...


    #
    # SFX & SFX Playback
    #

    # Main thread only
    def play_music(self, path): ...
    def stop_music(self): ...
    def fade_music(self): ...

    # Worker thread friendly
    def get_generator(self) -> DarkWaveGenerator: ...
    def play_sound(self, input_wave: DarkWave | DarkWaveStereo) -> int: ...
    def get_handle(self, sfx_handle_id: int) -> PlaySfxHandle: ...

    # Main thread only
    def render(self): ...