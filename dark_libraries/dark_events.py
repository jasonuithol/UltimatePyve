from dark_libraries.logging import LoggerMixin
from models.global_location import GlobalLocation

class DarkEventService(LoggerMixin):

    def __init__(self):
        self._party_location: GlobalLocation = None
        self._dark_event_listeners = list['DarkEventListenerMixin']()
        super().__init__()

    def subscribe(self, listener: 'DarkEventListenerMixin'):
        self._dark_event_listeners.append(listener)
        self.log(f"Added dark_event_listener: {listener.__class__.__name__}")

    def loaded(self, party_location: GlobalLocation):

        self.log(f"DEBUG: Propogating event 'loaded' to {len(self._dark_event_listeners)} listeners: {party_location}")

        for listener in self._dark_event_listeners:
            listener.loaded(party_location)

        self._party_location = party_location

    def pass_time(self, party_location: GlobalLocation):

        if party_location != self._party_location:
            if self._party_location.location_index != party_location.location_index or self._party_location.level_index != party_location.level_index:
                self._level_changed(party_location)
            self._party_moved(party_location)

        self.log(f"DEBUG: Propogating event 'pass_time' to {len(self._dark_event_listeners)} listeners: {party_location}")

        for listener in self._dark_event_listeners:
            listener.pass_time(party_location)

        self._party_location = party_location

    def _level_changed(self, party_location: GlobalLocation):
        self.log(f"DEBUG: Propogating event 'level_changed' to {len(self._dark_event_listeners)} listeners: {self._party_location} -> {party_location}")
        for listener in self._dark_event_listeners:
            listener.level_changed(party_location)

    def _party_moved(self, party_location: GlobalLocation):
        self.log(f"DEBUG: Propogating event 'party_moved' to {len(self._dark_event_listeners)} listeners: {self._party_location} -> {party_location}")
        for listener in self._dark_event_listeners:
            listener.party_moved(party_location)



# models
class DarkEventListenerMixin:

    # Injectable
    dark_event_service: DarkEventService

    def _after_inject(self):
        self.dark_event_service.subscribe(self)

    def loaded(self, party_location: GlobalLocation):
        return

    def pass_time(self, party_location: GlobalLocation):
        return

    def level_changed(self, party_location: GlobalLocation):
        return

    def party_moved(self, party_location: GlobalLocation):
        return
    
