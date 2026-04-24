from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math   import Coord
from dark_libraries.logging     import LoggerMixin

from data.global_registry        import GlobalRegistry
from models.agents.town_npc_agent import TownNpcAgent
from models.global_location      import GlobalLocation

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
        # Exit is handled automatically: NpcServiceImplementation's unfreeze
        # replaces _active_npcs with the frozen overworld set, discarding our town NPCs.

        # TODO: respawn when changing floors within the same location.

        self._party_location = party_location

    def party_moved(self, party_location: GlobalLocation):
        self._party_location = party_location

    def _spawn_for(self, party_location: GlobalLocation):
        section = self.global_registry.npc_sections.get(party_location.location_index)
        if section is None:
            self.log(f"DEBUG: No NPC section registered for location_index={party_location.location_index}")
            return

        hour = self.world_clock.get_natural_time().hour
        target_floor = party_location.level_index

        spawned = 0
        skipped_floor = 0
        skipped_sprite = 0
        for slot_index, schedule in enumerate(section.schedules):
            if schedule.is_empty():
                continue

            slot = schedule.slot_for_hour(hour)
            if schedule.z_coords[slot] != target_floor:
                skipped_floor += 1
                continue

            type_byte = section.types[slot_index]
            tile_id = type_byte + 0x100  # Redux: CharacterType + 0x100 = NPCKeySprite
            sprite = self.global_registry.sprites.get(tile_id)
            if sprite is None:
                self.log(f"WARN: No sprite for tile_id={tile_id} (type_byte={type_byte}) at slot={slot_index}")
                skipped_sprite += 1
                continue

            coord = Coord[int](schedule.x_coords[slot], schedule.y_coords[slot])
            name = f"NPC#{slot_index}"
            npc = TownNpcAgent(
                coord=coord,
                sprite=sprite,
                tile_id=tile_id,
                name=name,
                dialog_number=section.dialog_numbers[slot_index],
            )
            self.npc_service.add_npc(npc)
            spawned += 1

        self.log(
            f"Spawned {spawned} town NPCs at location_index={party_location.location_index} "
            f"floor={target_floor} hour={hour} "
            f"(skipped_floor={skipped_floor}, skipped_sprite={skipped_sprite})"
        )
