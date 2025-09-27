from pathlib import Path
from typing import Iterable


class TransportModeRegistry:

    def _after_inject(self):
        self._transport_modes = [
            "walk",
            "horse",
            "carpet",
            "skiff",
            "ship",
            "sail"
        ]
        self._transport_mode_soundtracks = dict(self.load_modded_soundtracks())

    def get_transport_mode(self, mode: int):
        return self._transport_modes[mode]
    
    def get_transport_mode_soundtrack(self, mode: int):
        return self._transport_mode_soundtracks.get(mode, None)

    def load_modded_soundtracks(self) -> Iterable[tuple[int, str]]:
        mods_dir = Path("mods")
        if not mods_dir.exists():
            return
        for mod_contents in mods_dir.iterdir():
            if mod_contents.is_dir:
                music_dir = mod_contents.joinpath("music")
                if music_dir.exists():
                    transport_dir = music_dir.joinpath("transport")
                    if transport_dir.exists():
                        for transport_soundtrack in transport_dir.iterdir():
                            transport_mode = int(transport_soundtrack.stem)
                            yield transport_mode, str(transport_soundtrack.absolute())
                            print(f"[mods.{mod_contents.stem}] Loaded transport mode soundtrack override for transport_mode_index={transport_mode} from {transport_soundtrack.name}")