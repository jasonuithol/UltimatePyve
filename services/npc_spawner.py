from typing import Protocol

from data.global_registry import GlobalRegistry

from models.npc_agent import NpcAgent
from services.npc_service import NpcService
from models.npc_state import NpcState

class NpcSpawner(Protocol):

    # Injectable
    global_registry: GlobalRegistry
    npc_service:     NpcService

    def _spawn_npc(self, npc_tile_id: int, npc_state: NpcState):
        sprite = self.global_registry.sprites.get(npc_tile_id)
        npc_agent = NpcAgent(npc_tile_id, sprite, npc_state)

        self.npc_service.add_npc(npc_agent)

    def pass_time(self):
        ...