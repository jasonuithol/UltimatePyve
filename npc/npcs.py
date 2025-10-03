from enum import Enum
from typing import Protocol

import pygame

from animation.sprite import Sprite
from animation.sprite_registry import SpriteRegistry
from dark_libraries.dark_math import Coord
from dark_libraries.service_provider import ServiceProvider
from display.interactive_console import InteractiveConsole
from display.tileset import TileRegistry
from game.interactable.interactable import Interactable, MoveIntoResult
from game.player_state import PlayerState
from maps.u5map_registry import U5MapRegistry

class NpcTileId(Enum):
    pass

class HumanTileId(Enum):
    WIZARD = 320
    BARD = 324
    FIGHTER = 328
    AVATAR = 332
    TOWNSFOLD = 336
    MERCHANT = 340
    JESTER = 344
    MUSICIAN = 348
    IN_STOCKS = 352
    IN_CHAINS = 356
    CHILD = 360
    BEGGAR = 364
    GUARD = 368
    BRITISH_GHOST = 372
    BLACKTHORN = 376
    LORD_BRITISH = 380

class MonsterTileId(Enum):
    SEAHORSE = 384
    SQUID = 388
    SEA_SERPENT = 392
    SHARK = 396
    GIANT_RAT = 400
    BAT = 404
    GIANT_SPIDER = 408
    GHOST = 412
    SLIME = 416
    GREMLIN = 420
    MIMIC = 424
    REAPER = 428
    GAZER = 432
    # gap
    GARGOYLE = 440
    INSECT_SWARM = 444
    ORC = 448
    SKELETON = 452
    PYTHON = 456
    ETTIN = 460
    HEADLESS = 464
    WISP = 468
    DAEMON = 472
    DRAGON = 476
    SAND_TRAP = 480
    TROLL = 484
    #gap
    MONGBAT = 496
    CORPSER = 500
    ROT_WORM = 504
    SHADOWLORD = 508


NUM_FRAMES = 4

class NpcSpriteFactory:

    # Injectable
    tile_registry: TileRegistry
    sprite_registry: SpriteRegistry

    def _register_enum_sprites(self, tile_enum: type[Enum], num_frames: int):
        for enum_name, enum_value in tile_enum.__members__.items():
            tile_id = enum_value.value
            s = Sprite(
                frames      = [self.tile_registry.tiles[i] for i in range(tile_id, tile_id + num_frames)],
                frame_time  = 0.5 if num_frames < 3 else 0.3
            )
            self.sprite_registry.register_animated_tile(tile_id, s)
            print(f"[sprites] Registered animated {tile_enum.__name__} {enum_name} with {num_frames} frames.")

    def register_npc_sprites(self):
        self._register_enum_sprites(HumanTileId, NUM_FRAMES)
        self._register_enum_sprites(MonsterTileId, NUM_FRAMES)

#
# Thing that the NPC CAN DO
#
class NpcState(Protocol):
    def __init__(self, coord: Coord):

        self.coord = coord
        self.player_state: PlayerState = ServiceProvider.get_provider().resolve(PlayerState)

    def pass_time(self):
        ...


#
# Things that can be DONE TO the NPC
#
class NpcInteractable(Interactable):

    def __init__(self, tile_id: int, sprite: Sprite, npc_state: NpcState):
        self.tile_id = tile_id # ID of the first frame
        self.sprite = sprite
        self.npc_state = npc_state
        self.interactive_console: InteractiveConsole = ServiceProvider.get_provider().resolve(InteractiveConsole)

    def get_tile_id(self):
        return self.tile_id()
    
    # For Viewport.draw_map
    def get_current_tile_id(self) -> int:
        return self.sprite.get_current_frame_tile(pygame.time.get_ticks())

    # For main.run
    def pass_time(self):
        self.npc_state.pass_time()

    #
    # ACTION IMPLEMENTORS
    #

    def move_into(self) -> MoveIntoResult:
        return MoveIntoResult(False, False)
    
    def attack(self):
        self.interactive_console.print_ascii("Attacking !")

    def cast_spell_on(self):
        pass

class NpcSpawner(Protocol):
    def pass_time(self):
        ...

class NpcRegistry:

    u5_map_registry: U5MapRegistry
    monster_spawner: NpcSpawner

    def _after_inject(self):
        self.active_npcs: list[NpcInteractable] = []
        self.frozen_npcs: list[NpcInteractable] = None

    def load_level(self, location_index: int, level_index: int):
        pass

    def pass_time(self):
        for npc_interactable in self.active_npcs:
            npc_interactable.pass_time()

    def get_npcs(self):
        return self.active_npcs

    def add_npc(self, npc_interactable: NpcInteractable):
        self.active_npcs.append(npc_interactable)

    def remove_npc(self, npc_interactable: NpcInteractable):
        self.active_npcs.remove(npc_interactable)

    def freeze_active_npcs(self):
        self.frozen_npcs = self.active_npcs
        self.active_npcs = []

    def unfreeze_active_npcs(self):
        self.active_npcs = self.frozen_npcs
        self.frozen_npcs = []
