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

    def get_transport_mode(self, mode: int):
        return self._transport_modes[mode]