from dark_libraries.dark_math import Coord

from game.map_content.map_content_registry import MapContentRegistry

from .npc_interactable import NpcInteractable

class NpcRegistry:

    # Injectable
    map_content_registry: MapContentRegistry

    def _after_inject(self):
        self.active_npcs: list[NpcInteractable] = []
        self.frozen_npcs: list[NpcInteractable] = None

    def _freeze_active_npcs(self):
        self.frozen_npcs = self.active_npcs
        self.active_npcs = []

    def _unfreeze_active_npcs(self):
        self.active_npcs = self.frozen_npcs
        self.frozen_npcs = []

    def load_level(self, location_index: int, level_index: int):
        self.location_index = location_index
        self.level_index = level_index

    def set_player_coord(self, player_coord: Coord):
        self.player_coord = player_coord

    def pass_time(self):

        map_level_contents = self.map_content_registry.get_map_level_contents(self.location_index, self.level_index)

        blocked_coords: set[Coord] = {
            coord
            # TODO: make a method for this ?
            for coord, coord_content in map_level_contents._data.items()
            if coord_content.get_terrain().walk == True
        }

        occupied_coords = {npc.get_coord() for npc in self.active_npcs}
        occupied_coords.add(self.player_coord)

        for npc in self.active_npcs:
            old_coord = npc.get_coord()
            npc.pass_time(blocked_coords.union(occupied_coords), self.player_coord)
            new_coord = npc.get_coord()
            if old_coord != new_coord:
                occupied_coords.add(new_coord)
                occupied_coords.remove(old_coord)
                map_level_contents.move_npc(old_coord, new_coord)

    def get_npcs(self):
        return self.active_npcs

    def add_npc(self, npc_interactable: NpcInteractable):
        self.active_npcs.append(npc_interactable)

    def remove_npc(self, npc_interactable: NpcInteractable):
        self.active_npcs.remove(npc_interactable)

