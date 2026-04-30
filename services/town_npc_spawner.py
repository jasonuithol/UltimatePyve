from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math   import Coord
from dark_libraries.logging     import LoggerMixin

from data.global_registry        import GlobalRegistry
from models.agents.town_npc_agent import TownNpcAgent
from models.global_location      import GlobalLocation
from models.npc_file              import NpcMapSection

from services.npc_service  import NpcService
from services.world_clock  import WorldClock


class TownNpcSpawner(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    global_registry: GlobalRegistry
    npc_service:     NpcService
    world_clock:     WorldClock

    def __init__(self):
        super().__init__()
        self._party_location: GlobalLocation = None
        self._recruited: dict[int, set[int]] = {}
        # slot_index -> currently-active TownNpcAgent on the player's level.
        # Cleared whenever NPCs are despawned (level change, recruit, schedule
        # transition that moves the NPC off the player's level).
        self._spawned: dict[int, TownNpcAgent] = {}

    def mark_recruited(self, location_index: int, dialog_number: int):
        # Suppress this dialog_number from spawning at this location after
        # the avatar recruits the NPC into the party.
        self._recruited.setdefault(location_index, set()).add(dialog_number)

    def loaded(self, party_location: GlobalLocation):
        self._party_location = party_location
        if party_location.location_index != 0:
            self._spawn_for(party_location)

    def level_changed(self, party_location: GlobalLocation):
        # NpcServiceImplementation.level_changed runs BEFORE this one (earlier subscription),
        # so on entry its freeze has already emptied _active_npcs; we can populate it cleanly.
        was_outer  = self._party_location.location_index == 0
        is_outer   = party_location.location_index == 0
        if was_outer and not is_outer:
            self._spawn_for(party_location)
        if not was_outer and is_outer:
            # Leaving a town: NPCs are frozen by NpcServiceImplementation, so drop our tracking.
            self._spawned.clear()
        # Exit is handled automatically: NpcServiceImplementation's unfreeze
        # replaces _active_npcs with the frozen overworld set, discarding our town NPCs.

        # TODO: respawn when changing floors within the same location.

        self._party_location = party_location

    def party_moved(self, party_location: GlobalLocation):
        self._party_location = party_location

    def get_spawned(self) -> dict[int, TownNpcAgent]:
        return self._spawned

    def spawn_slot(self, section: NpcMapSection, slot_index: int, party_location: GlobalLocation) -> TownNpcAgent | None:
        if slot_index in self._spawned:
            return self._spawned[slot_index]

        schedule = section.schedules[slot_index]
        if schedule.is_empty():
            return None

        recruited_dialog_numbers = self._recruited.get(party_location.location_index, set())
        if section.dialog_numbers[slot_index] in recruited_dialog_numbers:
            return None

        hour = self.world_clock.get_natural_time().hour
        slot = schedule.slot_for_hour(hour)
        if schedule.z_coords[slot] != party_location.level_index:
            return None

        type_byte = section.types[slot_index]
        tile_id = type_byte + 0x100  # Redux: CharacterType + 0x100 = NPCKeySprite
        sprite = self.global_registry.sprites.get(tile_id)
        if sprite is None:
            self.log(f"WARN: No sprite for tile_id={tile_id} (type_byte={type_byte}) at slot={slot_index}")
            return None

        coord = Coord[int](schedule.x_coords[slot], schedule.y_coords[slot])
        npc = TownNpcAgent(
            coord=coord,
            sprite=sprite,
            tile_id=tile_id,
            name=f"NPC#{slot_index}",
            dialog_number=section.dialog_numbers[slot_index],
        )
        self.npc_service.add_npc(npc)
        self._spawned[slot_index] = npc
        return npc

    def despawn_slot(self, slot_index: int):
        npc = self._spawned.pop(slot_index, None)
        if npc is None:
            return
        self.npc_service.remove_npc(npc)

    def _spawn_for(self, party_location: GlobalLocation):
        section = self.global_registry.npc_sections.get(party_location.location_index)
        if section is None:
            self.log(f"DEBUG: No NPC section registered for location_index={party_location.location_index}")
            return

        self._spawned.clear()
        spawned = 0
        for slot_index in range(len(section.schedules)):
            if self.spawn_slot(section, slot_index, party_location) is not None:
                spawned += 1

        hour = self.world_clock.get_natural_time().hour
        self.log(
            f"Spawned {spawned} town NPCs at location_index={party_location.location_index} "
            f"floor={party_location.level_index} hour={hour}"
        )
