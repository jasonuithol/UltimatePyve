from dark_libraries.logging import LoggerMixin
from models.agents.npc_agent import NpcAgent
from models.global_location import GlobalLocation

# ==================================================================================
#
# WARNING: Objects that are passed in by events should avoid also raising events !
#
# (you'll get circular dependencies.  You'd have to create interfaces. At least)
#
# ==================================================================================

class DarkEventService(LoggerMixin):

    def __init__(self):
        self._party_location: GlobalLocation = None
        self._dark_event_listeners = list[DarkEventListenerMixin]()
        super().__init__()

    def _log_event(self, event_name: str):
        self.log(f"DEBUG: Propogating event '{event_name}' to {len(self._dark_event_listeners)} listeners")

    def subscribe(self, listener: DarkEventListenerMixin):
        self._dark_event_listeners.append(listener)
        self.log(f"Added dark_event_listener: {listener.__class__.__name__}")

    #
    # Events
    #
    def loaded(self, party_location: GlobalLocation):

        self._log_event("loaded")

        for listener in self._dark_event_listeners:
            listener.loaded(party_location)

        self._party_location = party_location

    def pass_time(self, party_location: GlobalLocation):

        if party_location != self._party_location:
            if self._party_location.location_index != party_location.location_index or self._party_location.level_index != party_location.level_index:
                self._level_changed(party_location)
            self._party_moved(party_location)

        self._log_event("pass_time")

        for listener in self._dark_event_listeners:
            listener.pass_time(party_location)

        self._party_location = party_location

    def _level_changed(self, party_location: GlobalLocation):
        self._log_event("level_changed")
        for listener in self._dark_event_listeners:
            listener.level_changed(party_location)

    def _party_moved(self, party_location: GlobalLocation):
        self._log_event("party_moved")
        for listener in self._dark_event_listeners:
            listener.party_moved(party_location)

    def quit(self):
        self._log_event("quit")
        for listener in self._dark_event_listeners:
            listener.quit()

    def started_hosting(self):
        self._log_event("started_hosting")
        for listener in self._dark_event_listeners:
            listener.started_hosting()

    def stopped_hosting(self):
        self._log_event("stopped_hosting")
        for listener in self._dark_event_listeners:
            listener.stopped_hosting()
    
    def joined_server(self):
        self._log_event("joined_server")
        for listener in self._dark_event_listeners:
            listener.joined_server()
    
    def left_server(self):
        self._log_event("left_server")
        for listener in self._dark_event_listeners:
            listener.left_server()

    def npc_added(self, agent: NpcAgent):
        self._log_event("npc_added")
        for listener in self._dark_event_listeners:
            listener.npc_added(agent)
    
    def npc_removed(self, agent: NpcAgent):
        self._log_event("npc_removed")
        for listener in self._dark_event_listeners:
            listener.npc_removed(agent)

    def npc_moved(self, agent: NpcAgent):
        self._log_event("npc_moved")
        for listener in self._dark_event_listeners:
            listener.npc_moved(agent)

class DarkEventListenerMixin:

    # Injectable
    dark_event_service: DarkEventService

    def _after_inject(self):
        self.dark_event_service.subscribe(self)

        # TODO: get rid of this crap
        self._has_quit = False

    #
    # Application events.
    #
    def loaded(self, party_location: GlobalLocation):
        return

    def quit(self):

        # TODO: get rid of this crap
        self._has_quit = True

        return

    #
    # Player action events
    #
    def pass_time(self, party_location: GlobalLocation):
        return

    def level_changed(self, party_location: GlobalLocation):
        return

    def party_moved(self, party_location: GlobalLocation):
        return
    
    #
    # Multiplayer events
    #
    def started_hosting(self):
        return
    
    def stopped_hosting(self):
        return
    
    def joined_server(self):
        return
    
    def left_server(self):
        return

    def npc_added(self, agent: NpcAgent):
        return
    
    def npc_removed(self, agent: NpcAgent):
        return
    
    def npc_moved(self, agent: NpcAgent):
        return

    