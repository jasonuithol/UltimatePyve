from typing import Optional
from game.terrain import Terrain

class TerrainRegistry:

    def _after_inject(self):
        self._terrains: dict[int, Terrain] = dict()

    def register_terrain(self, tile_id: int, terrain: Terrain):
        self._terrains[tile_id] = terrain

    def get_terrain(self, tile_id: int) -> Optional[Terrain]:
        return self._terrains[tile_id]

    def can_traverse(self, transport_mode: str, tile_id: int) -> bool:
        terrain = self._terrains.get(tile_id, None)
        if terrain:
            return getattr(terrain, transport_mode)
        else:
            raise KeyError("TerrainRegistry has not been initialised.")
