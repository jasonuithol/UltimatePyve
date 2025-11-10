# file: display/display_engine.py
from typing import Protocol

class DisplayService(Protocol):

    # Main thread only
    def init(self): ...
    def render(self): ...

    # Worker thread safe
    def set_window_title(self, window_title: str): ...

