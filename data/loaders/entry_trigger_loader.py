from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.global_location import GlobalLocation
from models.terrain import Terrain
from models.u5_map import U5Map

class EntryTriggerLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    #
    # TODO: Dungeons, Shrines, Whirlpool, Moongates(?), Codex
    #
    def load(self):

        xs = list(self.global_registry.data_ovl.location_x_coords)
        ys = list(self.global_registry.data_ovl.location_y_coords)

        for trigger_index, (x, y) in enumerate(zip(xs, ys)):

            entry_map: U5Map = self.global_registry.maps.get(0)
            entry_coord = Coord[int](x,y)

            entry_point = None
            for checkable_level_index in [
                0,  # overworld 
                255 # underworld
            ]:
                entry_tile_id = entry_map.get_tile_id(checkable_level_index, entry_coord)
                entry_terrain: Terrain = self.global_registry.terrains.get(entry_tile_id)

                if entry_terrain.entry_point == True:
                    entry_point = GlobalLocation(0, checkable_level_index, entry_coord)
                    break
                else:
                    self.log(f"WARNING: Cannot find enterable terrain at coord={entry_coord}, tile_id={entry_tile_id} for world level {checkable_level_index}")

            assert entry_point, f"Cannot find enterable terrain at coord={entry_coord} for either the overworld or underworld."

            exit_u5map: U5Map = None
            for potential_exit in self.global_registry.maps.values():
                if potential_exit._location_metadata.trigger_index == trigger_index:
                    exit_u5map = potential_exit
                    break

            if exit_u5map is None:
                self.log(f"ERROR: Cannot find exit point for entry point={entry_point}. Skipping registration.")
                continue

            exit_point = GlobalLocation(
                exit_u5map.location_index,
                exit_u5map.default_level_index,
                Coord(
                    (exit_u5map.get_size().w - 1) // 2, 
                    exit_u5map.get_size().h - 2
                )
            )
            self.global_registry.entry_triggers.register(entry_point, exit_point)
            self.log(f"DEBUG: Registered trigger: entry={entry_point} (tile_id={entry_tile_id}) -> exit={exit_point} ({exit_u5map.name})")

        self.log(f"Loaded {len(self.global_registry.entry_triggers)} entry triggers into the over/under world")

