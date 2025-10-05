from typing import Protocol

from animation.sprite_registry import SpriteRegistry

from .npc_interactable import NpcInteractable
from .npc_registry import NpcRegistry
from .npc_state import NpcState

class NpcSpawner(Protocol):

    # Injectable
    sprite_registry: SpriteRegistry
    npc_registry: NpcRegistry

    def _spawn_npc(self, npc_tile_id: int, npc_state: NpcState):
        sprite = self.sprite_registry.get_sprite(npc_tile_id)
        npc_interactable = NpcInteractable(npc_tile_id, sprite, npc_state)

        self.npc_registry.add_npc(npc_interactable)

    def pass_time(self):
        ...