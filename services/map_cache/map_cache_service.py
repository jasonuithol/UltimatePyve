from dark_libraries.dark_math import Coord
from dark_libraries.logging   import LoggerMixin

from data.global_registry import GlobalRegistry

from models.terrain import Terrain
from models.tile    import TILE_ID_GRASS
from models.u5_map  import U5Map

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

    def cache_u5map(self, u5_map: U5Map):
        for level_index in u5_map.levels.keys():
            coord_contents_dict = dict[Coord, MapLevelContents]()            
            for coord in u5_map.get_coord_iteration():
                tile_id = u5_map.get_tile_id(level_index, coord)
                coord_contents_dict[coord] = CoordContents(
                    tile    = self.global_registry.tiles.get(tile_id),
                    terrain = self.global_registry.terrains.get(tile_id),
                    sprite  = self.global_registry.sprites.get(tile_id)
                )
            cache_key = u5_map.location_metadata.location_index, level_index
            self._map_level_content_dict[cache_key] = MapLevelContents(coord_contents_dict)
        self.log(f"Cached map {u5_map.location_metadata.name}")

    def get_coord_contents(self, location_index: int, level_index: int, coord: Coord) -> CoordContents:
        assert any(self._map_level_content_dict), "Must have a map cached"
        map_level_contents = self._map_level_content_dict[(location_index, level_index)]
        return map_level_contents.get_coord_contents(coord)
    
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
