"""
End-to-end conversation tests driven by ScriptedInputService.

Pattern: teleport into a town, inject a TownNpcAgent adjacent to the party
on the party_moved event (fires right after teleport), queue the Talk + keyword
keys, and read back what hit the console service.
"""
from pathlib import Path

import pygame
import pytest


TLK_FILE_NAMES = ("TOWNE.TLK", "CASTLE.TLK", "KEEP.TLK", "DWELLING.TLK")


def _find_u5_dir() -> Path | None:
    try:
        from configure import get_u5_path
        return get_u5_path()
    except AssertionError:
        pass
    repo_local = Path(__file__).resolve().parents[1] / "u5"
    if all((repo_local / name).exists() for name in TLK_FILE_NAMES):
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

    from dark_libraries.service_provider import ServiceProvider
    ServiceProvider._instance = None

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

    # Capture every print_ascii call so tests can assert on what the
    # conversation controller printed, without reaching into glyph/view state.
    from services.console_service import ConsoleService
    console = provider.resolve(ConsoleService)
    captured: list[str] = []
    original_print_ascii = console.print_ascii

    def _capturing_print_ascii(msg, *args, **kwargs):
        captured.append(msg if isinstance(msg, str) else "".join(chr(b) for b in msg))
        return original_print_ascii(msg, *args, **kwargs)

    console.print_ascii = _capturing_print_ascii

    yield type("Harness", (), {
        "provider":         provider,
        "party_controller": provider.resolve(PartyController),
        "party_agent":      provider.resolve(PartyController).party_agent,
        "npc_service":      provider.resolve(PartyController).npc_service,
        "scripted":         provider.resolve(InputService),
        "console_lines":    captured,
    })()


class _TownNpcInjector:
    """
    Listens for party_moved and places a TownNpcAgent adjacent to the party
    the first time the party arrives somewhere with known NPC dialogs.
    """

    def __init__(self, harness, dialog_number: int, name: str = "TestNpc"):
        self._harness = harness
        self._dialog_number = dialog_number
        self._name = name
        self._done = False
        self.injected_npc = None

    def loaded(self, loc): pass
    def level_changed(self, loc): pass
    def pass_time(self, loc): pass
    def quit(self): pass

    def party_moved(self, loc):
        if self._done:
            return
        registry = self._harness.party_controller.global_registry
        dialogs = registry.npc_dialogs.get(loc.location_index)
        if dialogs is None or self._dialog_number not in dialogs:
            return
        self._done = True

        from models.agents.town_npc_agent import TownNpcAgent
        from models.enums.npc_tile_id import NpcTileId

        tile_id = NpcTileId.MERCHANT.value
        sprite  = registry.sprites.get(tile_id)
        assert sprite is not None, "MERCHANT sprite should be registered"

        spawn_coord = loc.coord + (1, 0)
        npc = TownNpcAgent(
            coord         = spawn_coord,
            sprite        = sprite,
            tile_id       = tile_id,
            name          = self._name,
            dialog_number = self._dialog_number,
        )
        self._harness.npc_service.add_npc(npc)
        self.injected_npc = npc


def _pick_dialog_number(registry, location_index: int) -> int:
    dialogs = registry.npc_dialogs.get(location_index)
    assert dialogs, f"No dialogs registered for location {location_index}"
    return next(iter(dialogs.keys()))


def _britain_location_index(registry) -> int:
    britain = next(m for m in registry.maps.values() if m.name.upper() == "BRITAIN")
    return britain.location_index


def test_no_response_when_nobody_there(harness):
    # Talking into empty space should report "No response" and pass no time.
    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)

    harness.party_controller.run()

    lines = harness.console_lines
    assert any("No response" in line for line in lines), lines


def test_talk_prints_npc_greeting(harness):
    # Dialog for whichever dialog_number exists in Britain's TLK section.
    registry = harness.party_controller.global_registry
    # We can't peek yet — teleport has not fired. Inject lazily.
    injector = None

    def _late_setup():
        nonlocal injector
        loc_index = _britain_location_index(registry)
        dialog_number = _pick_dialog_number(registry, loc_index)
        injector = _TownNpcInjector(harness, dialog_number)
        from dark_libraries.dark_events import DarkEventService
        harness.provider.resolve(DarkEventService).subscribe(injector)

    _late_setup()

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("bye")  # terminates the conversation

    harness.party_controller.run()

    assert injector.injected_npc is not None, "Injector never fired"
    lines = harness.console_lines
    # The controller opens the conversation with the Description line,
    # prefixed by "You see " — matching U5's original intro.
    assert any(line.startswith("You see") for line in lines), lines


def test_talk_name_keyword_prints_npc_name(harness):
    registry = harness.party_controller.global_registry
    loc_index = _britain_location_index(registry)

    # Resolve the real dialog so we know what name to assert on.
    from dark_libraries.dark_events import DarkEventService
    # Harness hasn't teleported yet, so registry is already populated by init.
    dialog_number = _pick_dialog_number(registry, loc_index)
    dialog = registry.npc_dialogs.get(loc_index)[dialog_number]
    npc_name = dialog.name.as_text()
    assert npc_name, f"Dialog #{dialog_number} has empty name"

    injector = _TownNpcInjector(harness, dialog_number)
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("name")
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    lines = harness.console_lines
    # The Name line is only revealed when the Avatar asks. Response format:
    # "My name is {name}".
    name_hits = [line for line in lines if npc_name.lower() in line.lower()]
    assert any("my name is" in line.lower() for line in lines), lines
    assert len(name_hits) >= 1, (
        f"Expected NPC name {npc_name!r} to appear in the console, got {lines}"
    )


def test_unknown_keyword_gets_polite_deflection(harness):
    registry = harness.party_controller.global_registry
    from dark_libraries.dark_events import DarkEventService
    loc_index = _britain_location_index(registry)
    dialog_number = _pick_dialog_number(registry, loc_index)

    injector = _TownNpcInjector(harness, dialog_number)
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string("teleport britain")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("zzzz")  # guaranteed non-match
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    lines = harness.console_lines
    assert any("cannot help" in line.lower() for line in lines), lines
