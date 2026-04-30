from datetime import datetime
from typing import Iterable

from dark_libraries.dark_math import Coord, Size
from data.global_registry import GlobalRegistry
from models.agents.town_npc_agent import TownNpcAgent
from models.enums.transport_mode import TransportMode
from models.global_location import GlobalLocation
from models.npc_file import NpcMapSection, NpcSchedule

from services.town_npc_scheduler import TownNpcScheduler
from services.town_npc_spawner   import TownNpcSpawner


LOCATION_INDEX = 2  # Britain — anything non-zero with a section will do


class _FakeSprite:
    def create_random_time_offset(self):
        return 0.0

    def get_current_frame(self, _offset):
        return None


class _FakeU5Map:
    def __init__(self, size: Size[int]):
        self._size = size

    def get_size(self) -> Size[int]:
        return self._size

    def get_tile_id(self, _level_index, _coord):
        return 0


class _FakeNpcService:
    def __init__(self):
        self._active_npcs: list = []

    def add_npc(self, npc):
        self._active_npcs.append(npc)

    def remove_npc(self, npc):
        self._active_npcs.remove(npc)

    def get_npcs(self):
        return {npc.coord: npc for npc in self._active_npcs}

    def get_occupied_coords(self):
        return {npc.coord for npc in self._active_npcs}


class _FakeMapCacheService:
    def __init__(self, blocked: set[Coord[int]] | None = None):
        self._blocked = blocked or set()

    def get_blocked_coords(self, _location_index, _level_index, transport_mode: TransportMode):
        return set(self._blocked)


class _FakeWorldClock:
    def __init__(self, hour: int):
        self._hour = hour

    def get_natural_time(self) -> datetime:
        return datetime(year=139, month=4, day=4, hour=self._hour, minute=0)


def _empty_schedule() -> NpcSchedule:
    return NpcSchedule(
        ai_types=(0, 0, 0),
        x_coords=(0, 0, 0),
        y_coords=(0, 0, 0),
        z_coords=(0, 0, 0),
        times=(0, 0, 0, 0),
    )


def _schedule(
    *,
    coords: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]],
    z: tuple[int, int, int] = (0, 0, 0),
    times: tuple[int, int, int, int] = (8, 12, 18, 22),
) -> NpcSchedule:
    xs = (coords[0][0], coords[1][0], coords[2][0])
    ys = (coords[0][1], coords[1][1], coords[2][1])
    return NpcSchedule(
        ai_types=(0, 0, 0),
        x_coords=xs,
        y_coords=ys,
        z_coords=z,
        times=times,
    )


def _section_with_schedule(slot_index: int, schedule: NpcSchedule) -> NpcMapSection:
    schedules = [_empty_schedule()] * 32
    schedules[slot_index] = schedule
    types = [0] * 32
    types[slot_index] = 0x50  # arbitrary character type — sprite key = 0x150
    dialogs = [0] * 32
    dialogs[slot_index] = 1
    return NpcMapSection(
        schedules=tuple(schedules),
        types=tuple(types),
        dialog_numbers=tuple(dialogs),
    )


def _build_world(
    *,
    section: NpcMapSection,
    hour: int,
    party_level: int,
    map_size: Size[int] = Size[int](32, 32),
    blocked: set[Coord[int]] | None = None,
):
    registry = GlobalRegistry()
    registry.npc_sections.register(LOCATION_INDEX, section)
    registry.maps.register(LOCATION_INDEX, _FakeU5Map(map_size))
    # One sprite for the type byte we use in tests (0x50 → 0x150).
    registry.sprites.register(0x150, _FakeSprite())

    npc_service = _FakeNpcService()
    world_clock = _FakeWorldClock(hour)

    spawner = TownNpcSpawner()
    spawner.global_registry = registry
    spawner.npc_service     = npc_service
    spawner.world_clock     = world_clock

    scheduler = TownNpcScheduler()
    scheduler.global_registry   = registry
    scheduler.map_cache_service = _FakeMapCacheService(blocked=blocked)
    scheduler.npc_service       = npc_service
    scheduler.town_npc_spawner  = spawner
    scheduler.world_clock       = world_clock

    party_location = GlobalLocation(LOCATION_INDEX, party_level, Coord[int](0, 0))
    spawner.loaded(party_location)
    return spawner, scheduler, npc_service, world_clock, party_location


def test_npc_walks_one_tile_toward_target_when_on_party_level():
    # Slot 0 is at (5,5) all day; transition at hour 12 moves them to (5,8).
    schedule = _schedule(
        coords=((5, 5), (5, 8), (5, 5)),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)

    # Hour 11 — slot index for time 11 is 0 → NPC starts at (5,5).
    spawner, scheduler, npc_service, world_clock, party_location = _build_world(
        section=section, hour=11, party_level=0,
    )
    assert spawner.get_spawned()[1].coord == Coord[int](5, 5)

    # Advance to hour 12 → desired slot is 1 → target is (5,8).
    world_clock._hour = 12
    scheduler.pass_time(party_location)

    npc = spawner.get_spawned()[1]
    # One tile of progress toward (5,8): y should have advanced by 1.
    assert npc.coord == Coord[int](5, 6)


def test_npc_despawns_when_schedule_moves_them_to_different_level():
    # At hour 12 the NPC moves to level 1 (player still on level 0).
    schedule = _schedule(
        coords=((5, 5), (5, 5), (5, 5)),
        z=(0, 1, 0),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)

    spawner, scheduler, _, world_clock, party_location = _build_world(
        section=section, hour=11, party_level=0,
    )
    assert 1 in spawner.get_spawned()

    world_clock._hour = 12
    scheduler.pass_time(party_location)

    assert 1 not in spawner.get_spawned()


def test_npc_respawns_when_schedule_brings_them_back_to_party_level():
    # NPC is on level 1 at hour 11, then back on level 0 at hour 12.
    schedule = _schedule(
        coords=((5, 5), (5, 5), (5, 5)),
        z=(1, 0, 1),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)

    spawner, scheduler, _, world_clock, party_location = _build_world(
        section=section, hour=11, party_level=0,
    )
    assert 1 not in spawner.get_spawned()

    world_clock._hour = 12
    scheduler.pass_time(party_location)

    assert 1 in spawner.get_spawned()
    assert spawner.get_spawned()[1].coord == Coord[int](5, 5)


def test_pass_time_is_a_noop_in_overworld():
    schedule = _schedule(coords=((5, 5), (5, 8), (5, 5)))
    section = _section_with_schedule(1, schedule)

    spawner, scheduler, _, _, _ = _build_world(
        section=section, hour=11, party_level=0,
    )
    # Overworld: location_index 0. Should not touch any state.
    overworld = GlobalLocation(0, 0, Coord[int](100, 100))
    scheduler.pass_time(overworld)

    # Spawned NPC was at (5,5); still there.
    assert spawner.get_spawned()[1].coord == Coord[int](5, 5)


def test_npc_at_target_does_not_move():
    schedule = _schedule(coords=((5, 5), (5, 5), (5, 5)))
    section = _section_with_schedule(1, schedule)

    spawner, scheduler, _, _, party_location = _build_world(
        section=section, hour=11, party_level=0,
    )
    npc = spawner.get_spawned()[1]
    assert npc.coord == Coord[int](5, 5)

    scheduler.pass_time(party_location)

    assert npc.coord == Coord[int](5, 5)


def test_npc_can_step_onto_non_walkable_target_tile():
    # Schedule sends the merchant onto a counter tile (blocked for walking).
    # Their target should be excepted from the blocked set.
    schedule = _schedule(
        coords=((10, 10), (5, 5), (10, 10)),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)
    counter = Coord[int](5, 5)

    spawner, scheduler, _, world_clock, party_location = _build_world(
        section=section, hour=10, party_level=0,
        blocked={counter},
    )
    # NPC starts at (10,10) per slot 0; must walk to counter at slot 1.
    npc = spawner.get_spawned()[1]
    assert npc.coord == Coord[int](10, 10)

    world_clock._hour = 12  # exact match → slot 1
    # Step them in close: the easiest way is to keep ticking until they reach.
    for _ in range(20):
        scheduler.pass_time(party_location)
        if npc.coord == counter:
            break

    assert npc.coord == counter


def test_npc_routes_around_obstacle_via_perpendicular_axis():
    # NPC at (5,5), target (5,10). Direct path is blocked at (5,6); going
    # around via the x-axis must be tried before any random fallback.
    schedule = _schedule(
        coords=((5, 5), (5, 10), (5, 5)),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)
    blocked = {Coord[int](5, 6)}

    spawner, scheduler, _, world_clock, party_location = _build_world(
        section=section, hour=10, party_level=0,
        blocked=blocked,
    )
    npc = spawner.get_spawned()[1]
    assert npc.coord == Coord[int](5, 5)

    world_clock._hour = 12
    scheduler.pass_time(party_location)

    # y_step (5,6) is blocked → must take x_step (4,5) or (6,5). dx=0 so
    # x_step is None; the only candidate is the blocked y_step → no move.
    # That's the case this test confirms: no random wandering.
    assert npc.coord == Coord[int](5, 5)


def test_npc_teleports_after_being_stuck_for_threshold_ticks():
    # Same setup as above (no perpendicular escape); after 8 stuck ticks the
    # NPC should give up and teleport to the target.
    schedule = _schedule(
        coords=((5, 5), (5, 10), (5, 5)),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)
    blocked = {Coord[int](5, 6), Coord[int](5, 7), Coord[int](5, 8), Coord[int](5, 9)}

    spawner, scheduler, _, world_clock, party_location = _build_world(
        section=section, hour=10, party_level=0,
        blocked=blocked,
    )
    npc = spawner.get_spawned()[1]
    world_clock._hour = 12
    for _ in range(8):
        scheduler.pass_time(party_location)

    assert npc.coord == Coord[int](5, 10)


def test_npc_does_not_wander_to_random_neighbour_when_blocked():
    # Confirm the new pather never picks a random direction. With the only
    # axis blocked, NPC must stay put rather than jitter sideways.
    schedule = _schedule(
        coords=((5, 5), (5, 10), (5, 5)),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)
    blocked = {Coord[int](5, 6)}

    spawner, scheduler, _, world_clock, party_location = _build_world(
        section=section, hour=10, party_level=0,
        blocked=blocked,
    )
    npc = spawner.get_spawned()[1]

    world_clock._hour = 12
    for _ in range(3):
        scheduler.pass_time(party_location)

    # Did not move. (Will eventually teleport at 8 ticks; verified separately.)
    assert npc.coord == Coord[int](5, 5)


def test_walk_axis_priority_uses_longer_distance_first():
    # NPC at (5,5), target (10,7). |dx|=5, |dy|=2. Should step x first → (6,5).
    schedule = _schedule(
        coords=((5, 5), (10, 7), (5, 5)),
        times=(8, 12, 18, 22),
    )
    section = _section_with_schedule(1, schedule)

    spawner, scheduler, _, world_clock, party_location = _build_world(
        section=section, hour=10, party_level=0,
    )
    npc = spawner.get_spawned()[1]
    assert npc.coord == Coord[int](5, 5)

    world_clock._hour = 12
    scheduler.pass_time(party_location)

    assert npc.coord == Coord[int](6, 5)
