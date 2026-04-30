from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math   import Coord
from dark_libraries.logging     import LoggerMixin

from data.global_registry   import GlobalRegistry
from models.agents.town_npc_agent import TownNpcAgent
from models.enums.transport_mode import TransportMode
from models.global_location import GlobalLocation

from services.map_cache.map_cache_service import MapCacheService
from services.npc_service                  import NpcService
from services.town_npc_spawner             import TownNpcSpawner
from services.world_clock                  import WorldClock


# How many ticks (game minutes) an NPC is allowed to make zero progress
# toward its scheduled target before we give up and teleport it. Greedy
# axis-aligned stepping cannot route around complex obstacles (e.g. an
# armoury counter blocked from three sides), so this is the safety net
# that ensures merchants always end up at their station.
_STUCK_TELEPORT_THRESHOLD = 8


class TownNpcScheduler(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    global_registry:   GlobalRegistry
    map_cache_service: MapCacheService
    npc_service:       NpcService
    town_npc_spawner:  TownNpcSpawner
    world_clock:       WorldClock

    def __init__(self):
        super().__init__()
        # slot_index -> (last_target_coord, consecutive_failed_steps)
        self._stuck: dict[int, tuple[Coord[int], int]] = {}

    def pass_time(self, party_location: GlobalLocation):
        if party_location.location_index == 0:
            return

        section = self.global_registry.npc_sections.get(party_location.location_index)
        if section is None:
            return

        hour = self.world_clock.get_natural_time().hour
        spawned = self.town_npc_spawner.get_spawned()

        blocked_coords = self.map_cache_service.get_blocked_coords(
            party_location.location_index,
            party_location.level_index,
            transport_mode=TransportMode.WALK,
        )
        u5_map = self.global_registry.maps.get(party_location.location_index)
        boundary_rect = u5_map.get_size()

        for slot_index, schedule in enumerate(section.schedules):
            if schedule.is_empty():
                continue

            slot = schedule.slot_for_hour(hour)
            target_z = schedule.z_coords[slot]
            target_coord = Coord[int](schedule.x_coords[slot], schedule.y_coords[slot])

            on_party_level = target_z == party_location.level_index
            npc = spawned.get(slot_index)

            if not on_party_level:
                if npc is not None:
                    self.town_npc_spawner.despawn_slot(slot_index)
                self._stuck.pop(slot_index, None)
                continue

            if npc is None:
                self.town_npc_spawner.spawn_slot(section, slot_index, party_location)
                self._stuck.pop(slot_index, None)
                continue

            if npc.coord == target_coord:
                self._stuck.pop(slot_index, None)
                continue

            # An NPC's scheduled tile is by definition where they're meant to
            # stand — even if it's a non-walkable counter or bed. Allow stepping
            # onto it, and onto our own current tile.
            forbidden = (blocked_coords | self.npc_service.get_occupied_coords())
            forbidden.discard(npc.coord)
            forbidden.discard(target_coord)

            moved = self._step_towards(npc, target_coord, forbidden, boundary_rect)

            prev_target, prev_stuck = self._stuck.get(slot_index, (target_coord, 0))
            if prev_target != target_coord:
                prev_stuck = 0

            if moved:
                self._stuck[slot_index] = (target_coord, 0)
                continue

            stuck = prev_stuck + 1
            if stuck >= _STUCK_TELEPORT_THRESHOLD:
                self.log(f"NPC slot={slot_index} stuck for {stuck} ticks — teleporting to {target_coord}")
                npc.coord = target_coord
                self._stuck.pop(slot_index, None)
            else:
                self._stuck[slot_index] = (target_coord, stuck)

    def _step_towards(
        self,
        npc: TownNpcAgent,
        target_coord: Coord[int],
        forbidden_coords: set[Coord[int]],
        boundary_rect,
    ) -> bool:
        # Greedy axis-aligned: try the longer-distance axis first, fall back to
        # the perpendicular axis if that step is blocked. Never take a random
        # detour — town NPCs wandering away from their schedule looks broken.
        dx = target_coord.x - npc.coord.x
        dy = target_coord.y - npc.coord.y

        candidates: list[Coord[int]] = []
        x_step = Coord[int](npc.coord.x + (1 if dx > 0 else -1), npc.coord.y) if dx != 0 else None
        y_step = Coord[int](npc.coord.x, npc.coord.y + (1 if dy > 0 else -1)) if dy != 0 else None

        if abs(dx) >= abs(dy):
            if x_step is not None: candidates.append(x_step)
            if y_step is not None: candidates.append(y_step)
        else:
            if y_step is not None: candidates.append(y_step)
            if x_step is not None: candidates.append(x_step)

        for next_coord in candidates:
            if next_coord in forbidden_coords:
                continue
            if not boundary_rect.is_in_bounds(next_coord):
                continue
            npc.coord = next_coord
            return True
        return False
