from data.global_registry import GlobalRegistry

#
# TODO: THIS CLASS IS SCHEDULED FOR DEMOLITION (insane overengineering)
#

class TransportModeLoader:

    global_registry: GlobalRegistry

    def load(self):

        for index, transport_mode in enumerate([
            "walk",
            "horse",
            "carpet",
            "skiff",
            "ship",
            "sail"
        ]):
            self.global_registry.transport_modes.register(index, transport_mode)


