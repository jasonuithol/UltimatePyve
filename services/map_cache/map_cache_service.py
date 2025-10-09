from typing import Any
from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from data.global_registry import GlobalRegistry

from models.global_location import GlobalLocation
from models.terrain import Terrain
from models.tile    import TILE_ID_GRASS
from models.u5_map  import U5Map

from models.u5_map_level import U5MapLevel
from services.map_cache.coord_contents     import CoordContents
from services.map_cache.map_level_contents import MapLevelContents

class MapCacheService(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def __init__(self):
        super().__init__()
        self._map_level_content_dict = dict[tuple[int,int], MapLevelContents]()

    # Call this AFTER mods have loaded.
    def init(self):
        MapLevelContents.set_out_of_bounds_coord_content(
            CoordContents(
                tile         = self.global_registry.tiles.get(TILE_ID_GRASS),
                terrain      = Terrain(), # nothing is allowed out-of-bounds.
                sprite       = None
            )            
        )

        # cache every map
        for u5_map in self.global_registry.maps.values():
            self.cache_u5map(u5_map)
        self.log(f"Cached {len(self._map_level_content_dict)} maps")

    def cache_u5_map_level(self, cache_key: Any, u5_map_level: U5MapLevel):
        coord_contents_dict = dict[Coord, MapLevelContents]()            
        for coord, tile_id in u5_map_level:
            coord_contents_dict[coord] = CoordContents(
                tile    = self.global_registry.tiles.get(tile_id),
                terrain = self.global_registry.terrains.get(tile_id),
                sprite  = self.global_registry.sprites.get(tile_id)
            )

            assert not coord_contents_dict[coord].tile is None, "Cannot cache an empty or out-of-bounds tile."

        self._map_level_content_dict[cache_key] = MapLevelContents(coord_contents_dict)
        self.log(f"DEBUG: Cached map level; key={cache_key}, type={u5_map_level.__class__.__name__}, size={len(coord_contents_dict)}")

    def cache_u5map(self, u5_map: U5Map):
        for level_index, u5_map_level in u5_map:
            cache_key = u5_map.location_index, level_index
            self.cache_u5_map_level(cache_key, u5_map_level)

    def get_location_contents(self, global_location: GlobalLocation) -> CoordContents:
        assert any(self._map_level_content_dict), "Must have a map cached"
        map_level_contents = self._map_level_content_dict[(global_location.location_index, global_location.level_index)]
        return map_level_contents.get_coord_contents(global_location.coord)
    
    def get_map_level_contents(self, location_index: int, level_index: int) -> MapLevelContents:
        return self._map_level_content_dict[(location_index, level_index)]

    def get_blocked_coords(self, location_index: int, level_index: int, transport_mode_index: int) -> set[Coord]:
        map_level_contents: MapLevelContents = self.get_map_level_contents(location_index, level_index)
        transport_mode_name = self.global_registry.transport_modes.get(transport_mode_index)
        blocked_coords = {
            coord 
            for coord, coord_content in map_level_contents 
            if getattr(coord_content.get_terrain(), transport_mode_name) == False
        }
        return blocked_coords
