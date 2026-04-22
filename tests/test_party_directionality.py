import pytest

from dark_libraries.dark_math import Vector2
from models.agents.party_agent import PartyAgent
from models.enums.transport_mode import TransportMode

from controllers.party_controller import PartyController


class _FakeAvatarSpriteFactory:
    def __init__(self):
        self.calls = []

    def create_player(self, transport_mode: TransportMode, direction: int):
        self.calls.append((transport_mode, direction))
        return _FakeSprite()


class _FakeSprite:
    def create_random_time_offset(self):
        return 0.0


def _build_party_agent(transport_mode: TransportMode, last_east_west: int, last_nesw_dir: int):
    agent = PartyAgent()
    agent.avatar_sprite_factory = _FakeAvatarSpriteFactory()
    agent.set_transport_state(transport_mode, last_east_west, last_nesw_dir)
    return agent


def _build_controller(agent: PartyAgent) -> PartyController:
    controller = PartyController()
    controller.party_agent = agent
    return controller


#
# PartyAgent.get_transport_state direction selection
#
def test_walk_direction_is_always_zero():
    agent = _build_party_agent(TransportMode.WALK, last_east_west=1, last_nesw_dir=3)
    _, direction = agent.get_transport_state()
    assert direction == 0


@pytest.mark.parametrize("transport_mode", [TransportMode.HORSE, TransportMode.CARPET])
def test_east_west_modes_use_last_east_west(transport_mode):
    agent = _build_party_agent(transport_mode, last_east_west=1, last_nesw_dir=3)
    _, direction = agent.get_transport_state()
    assert direction == 1


@pytest.mark.parametrize("transport_mode", [TransportMode.SKIFF, TransportMode.SHIP, TransportMode.SAIL])
def test_nesw_modes_use_last_nesw_dir(transport_mode):
    agent = _build_party_agent(transport_mode, last_east_west=0, last_nesw_dir=2)
    _, direction = agent.get_transport_state()
    assert direction == 2


#
# PartyAgent.set_transport_state sprite refresh
#
def test_set_transport_state_rebuilds_sprite_via_factory():
    agent = _build_party_agent(TransportMode.SHIP, last_east_west=0, last_nesw_dir=0)
    factory: _FakeAvatarSpriteFactory = agent.avatar_sprite_factory

    agent.set_transport_state(TransportMode.SHIP, last_east_west=0, last_nesw_dir=2)

    # one call from the initial build, one from the turn.
    assert factory.calls == [
        (TransportMode.SHIP, 0),
        (TransportMode.SHIP, 2),
    ]


#
# PartyController._update_transport_state  - the regression we just fixed.
# Each move direction must rebuild the sprite with the new facing.
#
@pytest.mark.parametrize(
    "move_offset, expected_direction",
    [
        (Vector2[int]( 1,  0), 0),  # east  -> last_east_west = 0
        (Vector2[int](-1,  0), 1),  # west  -> last_east_west = 1
    ],
)
def test_horse_turn_refreshes_sprite(move_offset, expected_direction):
    agent = _build_party_agent(TransportMode.HORSE, last_east_west=0, last_nesw_dir=1)
    factory: _FakeAvatarSpriteFactory = agent.avatar_sprite_factory
    factory.calls.clear()

    controller = _build_controller(agent)
    controller._update_transport_state(move_offset)

    assert factory.calls == [(TransportMode.HORSE, expected_direction)]


@pytest.mark.parametrize(
    "move_offset, expected_direction",
    [
        (Vector2[int]( 1,  0), 0),
        (Vector2[int](-1,  0), 1),
    ],
)
def test_carpet_turn_refreshes_sprite(move_offset, expected_direction):
    agent = _build_party_agent(TransportMode.CARPET, last_east_west=0, last_nesw_dir=1)
    factory: _FakeAvatarSpriteFactory = agent.avatar_sprite_factory
    factory.calls.clear()

    controller = _build_controller(agent)
    controller._update_transport_state(move_offset)

    assert factory.calls == [(TransportMode.CARPET, expected_direction)]


@pytest.mark.parametrize(
    "move_offset, expected_direction",
    [
        (Vector2[int]( 0, -1), 0),  # north
        (Vector2[int]( 1,  0), 1),  # east
        (Vector2[int]( 0,  1), 2),  # south
        (Vector2[int](-1,  0), 3),  # west
    ],
)
@pytest.mark.parametrize("transport_mode", [TransportMode.SKIFF, TransportMode.SHIP, TransportMode.SAIL])
def test_nesw_transport_turn_refreshes_sprite(transport_mode, move_offset, expected_direction):
    agent = _build_party_agent(transport_mode, last_east_west=0, last_nesw_dir=0)
    factory: _FakeAvatarSpriteFactory = agent.avatar_sprite_factory
    factory.calls.clear()

    controller = _build_controller(agent)
    controller._update_transport_state(move_offset)

    assert factory.calls == [(transport_mode, expected_direction)]


def test_walk_turn_keeps_direction_zero():
    agent = _build_party_agent(TransportMode.WALK, last_east_west=0, last_nesw_dir=0)
    factory: _FakeAvatarSpriteFactory = agent.avatar_sprite_factory
    factory.calls.clear()

    controller = _build_controller(agent)
    controller._update_transport_state(Vector2[int](-1, 0))

    # walking never picks up a direction, even after a westward step.
    assert factory.calls == [(TransportMode.WALK, 0)]


def test_ship_preserves_east_west_after_vertical_move():
    # Heading east (direction=1), then stepping north should flip to direction=0
    # but stepping north shouldn't touch last_east_west on the agent.
    agent = _build_party_agent(TransportMode.SHIP, last_east_west=0, last_nesw_dir=1)
    factory: _FakeAvatarSpriteFactory = agent.avatar_sprite_factory
    factory.calls.clear()

    controller = _build_controller(agent)
    controller._update_transport_state(Vector2[int](0, -1))  # north

    assert agent.last_east_west == 0  # untouched by a vertical move
    assert agent.last_nesw_dir  == 0  # now facing north
    assert factory.calls == [(TransportMode.SHIP, 0)]
