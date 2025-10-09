from typing import Protocol

from data.global_registry import GlobalRegistry

from models.global_location import GlobalLocation
from models.npc_agent import NpcAgent

from services.npc_service import NpcService

class NpcSpawner(Protocol):

    def __init__(self):
        super().__init__()

    # Injectable
    global_registry: GlobalRegistry
    npc_service:     NpcService

    def _spawn_npc(self, npc_tile_id: int, global_location: GlobalLocation):
        sprite = self.global_registry.sprites.get(npc_tile_id)
        npc_metadata = self.global_registry.npc_metadata.get(npc_tile_id)
        npc_agent = NpcAgent(npc_tile_id, sprite, npc_metadata, global_location)

        self.npc_service.add_npc(npc_agent)

    def pass_time(self):
        ...