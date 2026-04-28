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


def _find_dialog_with_label_greeting(registry):
    """
    Find any (location_name, dialog_number, label) where the NPC's greeting
    is (or begins with) a label byte — a goto into that NPC's label section.
    Returns None if no such NPC exists in the current game data.
    """
    from models.tlk_file import is_label_byte, label_byte_to_num
    for loc_index, dialogs in registry.npc_dialogs.items():
        map_entry = registry.maps.get(loc_index)
        if map_entry is None:
            continue
        for dialog_number, dialog in dialogs.items():
            for item in dialog.greeting.items:
                if is_label_byte(item.command):
                    label = dialog.labels.get(label_byte_to_num(item.command))
                    if label is None:
                        continue
                    return map_entry.name, dialog_number, label
    return None


def _find_dialog_with_ask_name(registry, location_name: str):
    """
    Find a dialog in the given location whose Name line contains ASK_NAME.
    Returns (dialog_number, dialog) or None.
    """
    from models.tlk_file import TalkCommand
    loc_index = None
    for m in registry.maps.values():
        if m.name.upper() == location_name.upper():
            loc_index = m.location_index
            break
    if loc_index is None:
        return None
    dialogs = registry.npc_dialogs.get(loc_index, {})
    for dialog_number, dialog in dialogs.items():
        if dialog.name.contains_command(TalkCommand.ASK_NAME):
            return dialog_number, dialog
    return None


def _find_any_dialog_with_ask_name(registry):
    """Locate (location_name, dialog_number, dialog) for any NPC whose Name
    line contains ASK_NAME. Needed because not every town has such an NPC."""
    from models.tlk_file import TalkCommand
    for loc_index, dialogs in registry.npc_dialogs.items():
        map_entry = registry.maps.get(loc_index)
        if map_entry is None:
            continue
        for dialog_number, dialog in dialogs.items():
            if dialog.name.contains_command(TalkCommand.ASK_NAME):
                return map_entry.name, dialog_number, dialog
    return None


def _avatar_name_from_registry(registry) -> str:
    saved = registry.saved_game
    assert saved is not None, "Saved game must be loaded for avatar name"
    return saved.create_character_record(0).name


def test_greeting_that_is_a_label_byte_renders_the_label_text(harness):
    # Some NPCs (Eb the busboy is the canonical example) have a greeting
    # that is literally a label-byte goto. The controller should follow the
    # goto and render the label's initial_line, not an empty string.
    registry = harness.party_controller.global_registry
    found = _find_dialog_with_label_greeting(registry)
    if found is None:
        pytest.skip("No NPC with label-byte greeting in the current TLK data")
    location_name, dialog_number, label = found

    # Collect the label's entry text so we can assert it appears on screen.
    # The label's initial_line has [START_LABEL_DEFINITION, label_byte, ...text];
    # anything in the .text of its PlainString items counts as visible content.
    from models.tlk_file import TalkCommand
    visible = "".join(
        it.text for it in label.initial_line.items
        if it.command == TalkCommand.PLAIN_STRING
    ).strip()
    assert visible, (
        f"Test precondition: label {label.label_num} has no visible entry text — "
        "wouldn't prove rendering works"
    )

    from dark_libraries.dark_events import DarkEventService
    injector = _TownNpcInjector(harness, dialog_number)
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string(f"teleport {location_name.lower()}")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    lines = harness.console_lines
    # Compare case-insensitively since the label text may include quotes,
    # punctuation, and surrounding whitespace handled by the console wrapper.
    needle = visible.lower()
    assert any(needle in line.lower() for line in lines), (
        f"Expected label entry text {visible!r} to appear in console, got {lines}"
    )


def test_ask_name_with_correct_answer_sets_has_met(harness):
    # When the NPC's name line ends in ASK_NAME and the Avatar answers with
    # the correct name, the NPC should respond with the "pleasure" phrase and
    # the npc.has_met_avatar flag should be True afterwards.
    registry = harness.party_controller.global_registry
    found = _find_any_dialog_with_ask_name(registry)
    if found is None:
        pytest.skip("No NPC with ASK_NAME in the current TLK data")
    location_name, dialog_number, _dialog = found
    avatar_name = _avatar_name_from_registry(registry)

    from dark_libraries.dark_events import DarkEventService
    injector = _TownNpcInjector(harness, dialog_number)
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string(f"teleport {location_name.lower()}")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("name")
    harness.scripted.queue_string(avatar_name.lower())
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    lines = harness.console_lines
    assert any("pleasure" in line.lower() for line in lines), lines
    assert injector.injected_npc.has_met_avatar, (
        "has_met_avatar should be True after the Avatar introduces themselves"
    )


def _find_npc_by_name(registry, target_name: str, location_index: int | None = None):
    """Locate (location_name, dialog_number) for the first dialog whose Name
    line decodes to `target_name` (case-sensitive). If `location_index` is
    given, restrict the search to that location."""
    for loc_index, dialogs in registry.npc_dialogs.items():
        if location_index is not None and loc_index != location_index:
            continue
        map_entry = registry.maps.get(loc_index)
        if map_entry is None:
            continue
        for dialog_number, dialog in dialogs.items():
            if dialog.name.as_text() == target_name:
                return map_entry.name, dialog_number
    return None


def test_jeremy_keyword_keys_increments_party_keys_by_five(harness):
    # Jeremy the locksmith (Yew npc#20) hands over five keys when the Avatar
    # says "key". Doubles as a regression test for Yew's basement remap:
    # Yew has has_basement=True, so its U5Map._levels are keyed {0, 255}.
    # Before the basement-aware default_level fix, default_level was the raw
    # ordinal (1) and entry-trigger landed on a level that didn't exist.
    registry = harness.party_controller.global_registry
    yew_loc = next(
        m.location_index
        for m in registry.maps.values() if m.name.upper() == "YEW"
    )
    found = _find_npc_by_name(registry, "Jeremy", location_index=yew_loc)
    if found is None:
        pytest.skip("Jeremy not present in Yew's TLK data")
    location_name, dialog_number = found

    from models.enums.inventory_offset import InventoryOffset
    from models.party_inventory import PartyInventory
    party_inventory = harness.provider.resolve(PartyInventory)

    party_inventory.write(InventoryOffset.KEYS, 0)

    from dark_libraries.dark_events import DarkEventService
    injector = _TownNpcInjector(harness, dialog_number, name="Jeremy")
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string(f"teleport {location_name.lower()}")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("key")
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    assert party_inventory.read(InventoryOffset.KEYS) == 5, (
        f"Expected KEYS to rise from 0 to 5 after Jeremy's handover, got "
        f"{party_inventory.read(InventoryOffset.KEYS)}"
    )


def test_justin_keyword_mutton_y_increments_party_food(harness):
    # Playtest: Justin (Britain npc#7) sells mutton chops. The Avatar says
    # "mutt" to enter label0 ("Wouldst thou like to try a bite?"), then "y"
    # to accept — the label-scoped 'y' response fires CHANGE op=0x41 (FOOD).
    # Verifies the renderer's CHANGE handler increments PartyInventory.FOOD.
    registry = harness.party_controller.global_registry
    britain_loc = _britain_location_index(registry)
    found = _find_npc_by_name(registry, "Justin", location_index=britain_loc)
    if found is None:
        pytest.skip("Justin not present in Britain's TLK data")
    location_name, dialog_number = found

    from models.enums.inventory_offset import InventoryOffset
    from models.party_inventory import PartyInventory
    party_inventory = harness.provider.resolve(PartyInventory)

    party_inventory.write(InventoryOffset.FOOD, 0)
    food_before = party_inventory.read(InventoryOffset.FOOD)
    assert food_before == 0

    from dark_libraries.dark_events import DarkEventService
    injector = _TownNpcInjector(harness, dialog_number, name="Justin")
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string(f"teleport {location_name.lower()}")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("mutt")  # routes into label0
    harness.scripted.queue_string("y")     # accepts → CHANGE FOOD +1
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    assert party_inventory.read(InventoryOffset.FOOD) == 1, (
        f"Expected FOOD to rise by 1 after Justin's mutton handover, got "
        f"{party_inventory.read(InventoryOffset.FOOD)}"
    )


def test_description_render_does_not_apply_change(harness):
    # Description previews ('You see ...') run through _render_text_only,
    # which must NOT mutate party state even though Justin's keyword
    # responses contain CHANGE bytes. We verify by talking past the greeting
    # (which renders the description) and asking only non-CHANGE keywords.
    registry = harness.party_controller.global_registry
    britain_loc = _britain_location_index(registry)
    found = _find_npc_by_name(registry, "Justin", location_index=britain_loc)
    if found is None:
        pytest.skip("Justin not present in Britain's TLK data")
    location_name, dialog_number = found

    from models.enums.inventory_offset import InventoryOffset
    from models.party_inventory import PartyInventory
    party_inventory = harness.provider.resolve(PartyInventory)

    party_inventory.write(InventoryOffset.FOOD, 42)

    from dark_libraries.dark_events import DarkEventService
    injector = _TownNpcInjector(harness, dialog_number, name="Justin")
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string(f"teleport {location_name.lower()}")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("job")  # non-CHANGE keyword
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    assert party_inventory.read(InventoryOffset.FOOD) == 42, (
        "FOOD should be untouched when no CHANGE-bearing line is rendered"
    )


def test_ask_name_with_wrong_answer_leaves_has_met_false(harness):
    registry = harness.party_controller.global_registry
    found = _find_any_dialog_with_ask_name(registry)
    if found is None:
        pytest.skip("No NPC with ASK_NAME in the current TLK data")
    location_name, dialog_number, _dialog = found

    from dark_libraries.dark_events import DarkEventService
    injector = _TownNpcInjector(harness, dialog_number)
    harness.provider.resolve(DarkEventService).subscribe(injector)

    harness.scripted.queue_key(pygame.K_BACKQUOTE)
    harness.scripted.queue_string(f"teleport {location_name.lower()}")
    harness.scripted.queue_key(pygame.K_t)
    harness.scripted.queue_key(pygame.K_RIGHT)
    harness.scripted.queue_string("name")
    harness.scripted.queue_string("nobody")  # deliberately wrong
    harness.scripted.queue_string("bye")

    harness.party_controller.run()

    lines = harness.console_lines
    assert any("if you say so" in line.lower() for line in lines), lines
    assert not injector.injected_npc.has_met_avatar, (
        "has_met_avatar should stay False when the Avatar gives the wrong name"
    )
