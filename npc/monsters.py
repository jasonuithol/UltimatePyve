import math
import random

from dark_libraries.dark_math import Coord
from dark_libraries.service_provider import ServiceProvider

from animation.sprite_registry import SpriteRegistry
from display.interactive_console import InteractiveConsole
from game.player_state import PlayerState

from .npcs import MonsterTileId, NpcInteractable, NpcRegistry, NpcSpawner, NpcState

class MonsterState(NpcState):

    def __init__(self, coord: Coord):

        super().__init__(coord)
        
        self.interactive_console: InteractiveConsole = ServiceProvider.get_provider().resolve(InteractiveConsole)

        self.old_player_coord: Coord = None
        self.old_path: list[Coord] = None

    def _get_player_coord(self) -> Coord:
        _, _, p_coord = self.player_state.get_current_position()
        return p_coord

    def _build_new_path(self) -> list[Coord]:
        #
        # TODO: Get queried tiles.
        #
        player_coord = self._get_player_coord()

        if not self.old_path is None and len(self.old_path) > 0:

            if player_coord in self.old_path:
                print(f"[monster_state] Truncating existing path (player crossed existing path)")
                return self.old_path[0:self.old_path.index(player_coord)]

            for path_coord in self.old_path:
                if path_coord.taxi_distance(player_coord) == 1:
                    print(f"[monster_state] Truncating existing path (player moved closer)")
                    return self.old_path[0:self.old_path.index(path_coord) + 1]

            print(f"[monster_state] Extending existing path (player moved away)")
            path_to_extend = self.old_path        
                
        print(f"[monster_state] Building new path from {self.coord} to {player_coord}")
        path_to_extend: list[Coord] = [self.coord + self.coord.normal_4way(player_coord)]

        while path_to_extend[-1].taxi_distance(player_coord) > 1:
            new_move = path_to_extend[-1].normal_4way(player_coord)
            new_coord = path_to_extend[-1] + new_move
            if new_coord in path_to_extend:
                print(f"[monster_state] Truncating existing path to {new_coord} during extension (found a shortcut)")
                path_to_extend = path_to_extend[0:path_to_extend.index(new_coord)]

            path_to_extend.append(new_coord)

        return path_to_extend

    def _find_next_move(self) -> Coord:
        new_player_coord = self._get_player_coord()
        if self.old_path is None or len(self.old_path) == 0 or self.old_player_coord is None or self.old_player_coord != new_player_coord:
            self.old_path = self._build_new_path()
            self.old_player_coord = new_player_coord
        return self.old_path.pop(0)

    def _move(self):
        next_coord = self._find_next_move()
        assert self.coord.taxi_distance(next_coord) == 1, f"Cannot move directly from {self.coord} to {next_coord}"
        print(f"[monster_state] Moving from {self.coord} to {next_coord}")
        self.coord = next_coord

    def _attack(self):
        #
        # TODO: launch combat screen
        #
        self.interactive_console.print_ascii("Attacked !")

    def take_turn(self):
        player_coord = self._get_player_coord()
        if self.coord == player_coord:
            print("[monster_state] ERROR ! Monster and Player occupying same coord - skipping turn.")
        elif self.coord.taxi_distance(player_coord) == 1:
            self._attack()
        else:
            self._move()

    def pass_time(self):
        self.take_turn()

class MonsterSpawner(NpcSpawner):

    def __init__(self):
        pass

    MONSTER_SPAWN_DISTANCE: float = 10
    MONSTER_SPAWN_PROBABILITY: float = 0.1

    # INjectable
    player_state: PlayerState
    sprite_registry: SpriteRegistry
    npc_registry: NpcRegistry

    def pass_time(self):

        if random.randint(1,int(1/__class__.MONSTER_SPAWN_PROBABILITY)) > 1:
            # no monsters for you.
            return
        
        monster_tile_id_enum = random.choice(list(MonsterTileId))

        _, _, player_coord = self.player_state.get_current_position()
        monster_coord = player_coord.translate_polar(__class__.MONSTER_SPAWN_DISTANCE, random.uniform(-math.pi, math.pi))

        monster_state = MonsterState(monster_coord)
        sprite = self.sprite_registry.get_sprite(monster_tile_id_enum.value)
        npc_interactable = NpcInteractable(monster_tile_id_enum.value, sprite, monster_state)

        self.npc_registry.add_npc(npc_interactable)

        print(f"[monster_spawner] Spawned {monster_tile_id_enum.name} at {monster_coord}")
    
#
# MAIN
#

if __name__ == "__main__":

    class PlayerStateStub:
        def __init__(self, coord):
            self.coord = coord
        def get_current_position(self):
            return None, None, self.coord
        
    class InteractiveConsoleStub:
        def __init__(self):
            self.recorded_messages = []
        def print_ascii(self, msg):
            print(f"Received print_ascii msg={msg}")
            self.recorded_messages.append(msg)

    monster_coord = Coord(10,10)
    player_coord = Coord(20,20)

    monster_state = object.__new__(MonsterState)
    monster_state.player_state = PlayerStateStub(player_coord)
    monster_state.coord = monster_coord
    monster_state.interactive_console = InteractiveConsoleStub()
    monster_state.old_path = None
    monster_state.old_player_coord = None

    assert monster_state._get_player_coord() == player_coord, "Not obtaining correct player_coord."

    monster_state.pass_time()
    assert monster_state.old_player_coord == player_coord, "Not remembering correct player_coord."

    monster_state.pass_time()
    print(monster_state.old_path)

    expected_num_coords = monster_state.coord.taxi_distance(player_coord) - 1
    assert len(monster_state.old_path) == expected_num_coords, f"expected {expected_num_coords} coords, got {len(monster_state.old_path)}"

    for i in range(expected_num_coords + 1):
        monster_state.pass_time()
    assert "Attacked !" in monster_state.interactive_console.recorded_messages, "Did not attack"

    monster_state.coord = monster_coord
    monster_state.pass_time()

    player_coord = Coord(15,15)
    monster_state.player_state.coord = player_coord
    monster_state.pass_time()

    expected_num_coords = monster_state.coord.taxi_distance(player_coord) - 1
    assert monster_state.old_path[-1].taxi_distance(player_coord) == 1, "path did not terminate in coord adjacent to player"
    assert len(monster_state.old_path) == expected_num_coords, f"expected {expected_num_coords} coords, got {len(monster_state.old_path)}"

    player_coord = Coord(16,16)
    monster_state.player_state.coord = player_coord
    monster_state.pass_time()

    expected_num_coords = monster_state.coord.taxi_distance(player_coord) - 1
    assert monster_state.old_path[-1].taxi_distance(player_coord) == 1, "path did not terminate in coord adjacent to player"
    assert len(monster_state.old_path) == expected_num_coords, f"expected {expected_num_coords} coords, got {len(monster_state.old_path)}"

    print("All tests passed.")