import os
from pathlib import Path

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


@pytest.fixture(scope="module")
def u5_dir() -> Path:
    path = _find_u5_dir()
    if path is None:
        pytest.skip("U5 game files not found")
    return path


def test_boot_script_runs_spawn_tour_and_quits(u5_dir: Path, monkeypatch):
    # Headless display + audio.
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setenv("UPV_CONSOLE_SCRIPT", str(Path("dev/scripts/smoke_test.txt").resolve()))

    import pygame
    pygame.init()

    from dark_libraries.service_provider import ServiceProvider
    from service_composition            import compose
    from controllers.initialisation_controller import InitialisationController
    from controllers.party_controller          import PartyController

    provider = ServiceProvider()
    compose(provider)
    provider.inject_all()

    init = provider.resolve(InitialisationController)
    init.init(u5_dir)

    pygame.key.set_repeat(300, 50)
    try:
        pygame.mixer.init()
    except pygame.error:
        pass  # dummy audio sometimes refuses; safe to ignore in tests.

    party_controller = provider.resolve(PartyController)

    # If the smoke script's final `quit` doesn't fire, this test would hang
    # on pygame.event.get(); we assert by reaching the line after run().
    party_controller.run()

    # After the script's `quit`, we should land on the overworld
    # (the penultimate command is `spawn overworld`).
    current = party_controller.party_agent.get_current_location()
    assert current.location_index == 0
