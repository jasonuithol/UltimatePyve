"""
End-to-end gameplay tests driven by ScriptedInputService.

Each test boots the full game (DI graph, NPC loads, party init), queues
a sequence of keystrokes + console commands, runs party_controller.run()
until the queue drains, then asserts on service state. When the scripted
queue empties, ScriptedInputService fires dark_event_service.quit() so
the main loop exits naturally — tests don't need to queue an explicit
`quit` unless they want the console `quit` command specifically exercised.

Harness fixture
---------------
`harness` yields:
    provider         — ServiceProvider (for .resolve(...))
    party_controller — for .run() and .global_registry
    party_agent      — current location, party state
    npc_service      — spawned monsters, party members, frozen NPCs
    scripted         — the ScriptedInputService instance (queue_key etc.)

The fixture swaps the real InputServiceImplementation for ScriptedInput
after compose() but before inject_all(), so every service that wires
`input_service` gets the scripted one.

Queuing input
-------------
    harness.scripted.queue_key(pygame.K_UP)       # one KEYDOWN event
    harness.scripted.queue_keys(K_UP, K_UP, K_a)  # several in order
    harness.scripted.queue_string("teleport britain")
        # types each char as a KEYDOWN + trailing K_RETURN.
        # The console command controller auto-closes the console on
        # Enter, so don't queue another BACKQUOTE to close it.

A full console interaction is:
    queue_key(K_BACKQUOTE)            # open console
    queue_string("teleport britain")  # types + Enter (auto-closes)

Keystrokes fired outside the console (movement, attack) go straight to
the party controller's dispatch — no BACKQUOTE needed.

Mid-run event injection
-----------------------
Some tests can't pre-queue everything because the needed input depends
on runtime state (e.g. combat cursor coords aren't known until the
combat map is registered). Subscribe a listener to DarkEventService and
queue more events from inside a callback:

    from dark_libraries.dark_events import DarkEventService
    des = harness.provider.resolve(DarkEventService)

    class Injector:
        _done = False
        def loaded(self, loc): pass
        def level_changed(self, loc): pass
        def party_moved(self, loc): pass
        def quit(self): pass
        def pass_time(self, loc):
            if self._done or loc.location_index != COMBAT_MAP_LOCATION_INDEX:
                return
            self._done = True
            # inspect combat_map, compute deltas, queue more keys

    des.subscribe(Injector())

See test_combat_attack_lands_damage_on_monster for a working example.

RNG determinism
---------------
Combat hit rolls, NPC turn-order tiebreakers, and monster movement all
use the `random` module. For RNG-sensitive assertions, seed at the top
of the test: `random.seed(1)` (or any other constant).

Gotchas
-------
- One boot per test: the fixture resets ServiceProvider._instance and
  PartyAgent.location_stack / PartyAgent.party_members (both are
  class-level attributes — a pre-existing codebase wart) so tests don't
  leak state.
- `queue_string` is *console-mode* typing. Keys outside a-z / 0-9 / a
  small punctuation set are silently dropped — see _char_to_keycode in
  ScriptedInputService.
- If a queued command needs direction input (e.g. K_a for attack calls
  obtain_action_direction), queue the direction key immediately after.
"""
from pathlib import Path

import pygame
import pytest


NPC_FILE_NAMES = ("TOWNE.NPC", "DWELLING.NPC", "CASTLE.NPC", "KEEP.NPC")


def _find_u5_dir() -> Path | None:
    try:
        from configure import get_u5_path
        return get_u5_path()
    except AssertionError:
        pass
    repo_local = Path(__file__).resolve().parents[1] / "u5"
    if all((repo_local / name).exists() for name in NPC_FILE_NAMES):
        return repo_local
    return None


@pytest.fixture
def u5_dir() -> Path:
    path = _find_u5_dir()
    if path is None:
        pytest.skip("U5 game files not found")
    return path


@pytest.fixture
def harness(u5_dir, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.delenv("UPV_CONSOLE_SCRIPT", raising=False)

    # Reset the ServiceProvider singleton so repeated test boots work.
    from dark_libraries.service_provider import ServiceProvider
    ServiceProvider._instance = None

    # Reset class-level mutable state on PartyAgent (pre-existing codebase wart).
    from models.agents.party_agent import PartyAgent
    PartyAgent.location_stack = []
    PartyAgent.party_members  = []

    pygame.init()

    from service_composition import compose
    from services.input_service import InputService
    from service_implementations.input_service_implementation import InputServiceImplementation
    from service_implementations.scripted_input_service       import ScriptedInputService

    provider = ServiceProvider()
    compose(provider)

    # Drop the default input service and map the abstract onto the scripted one.
    provider._instances.pop(InputServiceImplementation, None)
    provider._mappings.pop(InputService, None)
    provider.register_mapping(InputService, ScriptedInputService)

    provider.inject_all()

    from controllers.initialisation_controller import InitialisationController
    from controllers.party_controller          import PartyController

    init = provider.resolve(InitialisationController)
    init.init(u5_dir)

    try:
        pygame.mixer.init()
    except pygame.error:
        pass

    party_controller = provider.resolve(PartyController)
    scripted         = provider.resolve(InputService)

    yield type("Harness", (), {
        "provider":         provider,
        "party_controller": party_controller,
        "party_agent":      party_controller.party_agent,
        "npc_service":      party_controller.npc_service,
        "scripted":         scripted,
    })()


def test_teleport_places_party_in_britain(harness):
    # Boot script equivalent: type at the console, press enter, then quit.
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("quit")

    harness.party_controller.run()

    current = harness.party_agent.get_current_location()
    britain_map = next(m for m in harness.party_controller.global_registry.maps.values() if m.name.upper() == "BRITAIN")
    assert current.location_index == britain_map.location_index


def test_party_moves_north_on_up_keypress(harness):
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    # Close console, press UP twice, then quit via console.
    start_getter = []
    harness.scripted.queue_key(pygame.K_UP)
    harness.scripted.queue_key(pygame.K_UP)
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("quit")

    # Capture coord right after teleport via a hook: easiest is to run once,
    # teleport, introspect, then queue moves. But run() consumes all events.
    # Instead, derive expected by looking at the known Britain entry.
    britain_map = next(m for m in harness.party_controller.global_registry.maps.values() if m.name.upper() == "BRITAIN")
    from dark_libraries.dark_math import Coord
    entry_coord = Coord[int](
        (britain_map.get_size().w - 1) // 2,
        britain_map.get_size().h - 2,
    )

    harness.party_controller.run()

    final = harness.party_agent.get_current_location()
    # Assert we moved at least one tile north (in case terrain blocks us
    # partway). Both UP presses succeeding gives y == entry.y - 2.
    assert final.location_index == britain_map.location_index
    assert final.coord.y < entry_coord.y, (
        f"Party should have moved north from entry {entry_coord}, got {final.coord}"
    )


def test_spawn_monster_places_agent_adjacent_to_party(harness):
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("spawn skeleton")
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("quit")

    harness.party_controller.run()

    party_coord = harness.party_agent.get_current_location().coord
    east = party_coord + (1, 0)
    npc = harness.npc_service.get_npc_at(east)
    assert npc is not None, f"Expected a monster at {east} after spawn"
    assert npc.name.upper() == "SKELETON"


def test_attack_east_enters_combat_mode(harness):
    # Teleport → spawn monster east → press A + Right to attack east.
    # Queue drain triggers quit inside combat's inner loop, which then exits
    # via _exit_combat_arena. Asserts that combat was actually entered.
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("spawn skeleton")
    harness.scripted.queue_key(pygame.K_a)      # Attack
    harness.scripted.queue_key(pygame.K_RIGHT)  # Direction: east

    harness.party_controller.run()

    from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX
    maps = harness.party_controller.global_registry.maps
    assert maps.get(COMBAT_MAP_LOCATION_INDEX) is not None, (
        "Combat map should have been registered after attacking adjacent monster"
    )
    # _exit_combat_arena removes the original enemy_party from the npc service.
    party_coord = harness.party_agent.get_current_location().coord
    east = party_coord + (1, 0)
    assert harness.npc_service.get_npc_at(east) is None, (
        "Original spawned skeleton should have been removed when combat tore down"
    )


def test_combat_attack_lands_damage_on_monster(harness):
    # Drive a full combat hit via keystrokes: enter combat, then once combat
    # fires its first pass_time, look up the combat map's spawn coords and
    # queue an `A` + direction sequence that aims the cursor from the party
    # member's spawn toward the monster's spawn. random is seeded so the hit
    # roll + turn-order tiebreakers are deterministic.
    import random as _random
    _random.seed(1)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("spawn skeleton")
    harness.scripted.queue_key(pygame.K_a)
    harness.scripted.queue_key(pygame.K_RIGHT)

    from dark_libraries.dark_events import DarkEventService
    from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX
    dark_event_service = harness.provider.resolve(DarkEventService)

    class CursorInjector:
        _done = False
        def loaded(self, loc): pass
        def level_changed(self, loc): pass
        def party_moved(self, loc): pass
        def quit(self): pass
        def pass_time(self, loc):
            if self._done or loc.location_index != COMBAT_MAP_LOCATION_INDEX:
                return
            self._done = True
            wrapper = harness.party_controller.global_registry.maps.get(COMBAT_MAP_LOCATION_INDEX)
            combat_map = wrapper.get_map_level(0)
            party_spawn   = combat_map._party_spawn_coords[0][0]
            monster_spawn = combat_map._monster_spawn_coords[0]
            dx = monster_spawn.x - party_spawn.x
            dy = monster_spawn.y - party_spawn.y
            # Cursor range for BARE_HANDS is 1, so it'll only travel 1 step
            # even if we queue more. That's fine — one step in the direction
            # of the enemy still triggers an attack against the adjacent tile.
            harness.scripted.queue_key(pygame.K_a)
            for _ in range(abs(dx)):
                harness.scripted.queue_key(pygame.K_RIGHT if dx > 0 else pygame.K_LEFT)
            for _ in range(abs(dy)):
                harness.scripted.queue_key(pygame.K_DOWN if dy > 0 else pygame.K_UP)
            harness.scripted.queue_key(pygame.K_RETURN)

    dark_event_service.subscribe(CursorInjector())

    harness.party_controller.run()

    # _last_attacked_monster holds a reference to every monster a party
    # member's cursor landed on. A hit lowers its hp below max; a killing
    # blow drops hp to zero and removes it from the npc service. Either
    # outcome proves keystroke-driven combat damage works end-to-end.
    from controllers.combat_controller import CombatController
    attacked_skeletons = [
        m for m in CombatController._last_attacked_monster.values()
        if m.name.upper() == "SKELETON"
    ]
    assert attacked_skeletons, "No skeleton was ever targeted by an attack"
    took_damage = any(m.hitpoints < m.maximum_hitpoints for m in attacked_skeletons)
    assert took_damage, (
        f"Expected at least one attacked skeleton to have taken damage, got "
        f"{[(m.name, m.hitpoints, m.maximum_hitpoints) for m in attacked_skeletons]}"
    )
