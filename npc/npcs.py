from enum import Enum

from animation.sprite import Sprite
from animation.sprite_registry import SpriteRegistry
from dark_libraries.dark_math import Coord
from display.tileset import TileRegistry
from game.player_state import PlayerState

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
    SOME_SORT_OF_VINE = 500 # TODO: get real name
    ROT_WORM = 504
    SHADOWLORD = 508


NUM_FRAMES = 4

class NpcSpriteFactory:

    # Injectable
    tile_registry: TileRegistry
    sprite_registry: SpriteRegistry

    def register_enum_sprites(self, tile_enum: NpcTileId, num_frames: int):
        for tile_id_enum in HumanTileId:
            tile_id = tile_id_enum.value
            s = Sprite(
                frames      = [self.tile_registry.tiles[i] for i in range(tile_id, tile_id + num_frames)],
                frame_time  = 0.5 if num_frames < 3 else 0.3
            )
            self.sprite_registry.register_animated_tile(tile_id, s)
            print(f"[sprites] Registered animated {tile_enum.__class__.name} {tile_id_enum.name} with {num_frames} frames.")

    def register_npc_sprites(self):
        self.register_enum_sprites(HumanTileId, NUM_FRAMES)
        self.register_enum_sprites(MonsterTileId, NUM_FRAMES)

#
# Thing that the NPC CAN DO
#
class NpcState:
    def __init__(self, sprite: Sprite, coord: Coord, player_state: PlayerState):
        self.sprite = sprite
        self.coord = coord

class MonsterState(NpcState):

    def _move(self):
        distance = self.coord

    def _attack(self):
        pass

    def take_turn(self):
        pass

#
# Things that can be DONE TO the NPC
#
class NpcInteractable:

    def pass_time(self):
        pass

    def attack(self):
        pass

    def cast_spell_on(self):
        pass
