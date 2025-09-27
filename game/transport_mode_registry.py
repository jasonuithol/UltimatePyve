class TransportModeRegistry:

    def _after_inject(self):
        self._transport_modes: list[str] = [
            "walk",
            "horse",
            "carpet",
            "skiff",
            "ship",
            "sail"
        ]
        self._transport_mode_soundtracks: dict[int, str] = {}

    def get_transport_mode(self, mode: int):
        return self._transport_modes[mode]
    
    def get_transport_mode_soundtrack(self, mode: int):
        return self._transport_mode_soundtracks.get(mode, None)

