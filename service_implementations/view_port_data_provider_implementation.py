from dark_libraries.dark_math import Coord, Rect

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.agents.npc_agent import NpcAgent
from models.agents.party_agent import PartyAgent
from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX
from models.tile import Tile

from models.u5_map_level import U5MapLevel
from models.u5_map import U5Map # for syntax highlighting
from services.field_of_view_calculator import FieldOfViewCalculator
from services.lighting_service import LightingService
from services.map_cache.map_cache_service import MapCacheService
from services.map_cache.map_level_contents import MapLevelContents
from services.npc_service import NpcService

from services.view_port_data_provider import ViewPortData

class ViewPortDataProviderImplementation(LoggerMixin):

    party_agent:              PartyAgent
    global_registry:          GlobalRegistry
    map_cache_service:        MapCacheService    
    field_of_view_calculator: FieldOfViewCalculator
    lighting_service:         LightingService
    npc_service:              NpcService

    def _after_inject(self):
        self._default_tile: Tile = None

    def set_default_tile(self, tile: Tile):
        self.log(f"DEBUG: Default tile set to: tile_id={tile.tile_id}")
        self._default_tile: Tile = tile

    def get_party_map_data(self, world_view_rect: Rect[int]) -> ViewPortData:

        party_location = self.party_agent.get_current_location()

        lighting_map = self._get_lighting_map(world_view_rect)
        terrain_map = self._get_terrain_map(party_location.location_index, party_location.level_index, world_view_rect)

        # apply lighting to terrain
        viewable_terrain_map = ViewPortData()

        for coord in world_view_rect:
            if coord in lighting_map:
                viewable_terrain_map[coord] = terrain_map[coord]
            else:
                viewable_terrain_map[coord] = self.global_registry.tiles.get(255) # Black, for being unlit or behind a wall

        return viewable_terrain_map

    def get_combat_map_data(self, world_view_rect: Rect[int]) -> ViewPortData:
        return self._get_terrain_map(
            location_index  = COMBAT_MAP_LOCATION_INDEX, 
            level_index     = 0, 
            world_view_rect = world_view_rect
        )

    def _get_terrain_map(self, location_index: int, level_index: int, world_view_rect: Rect[int]) -> ViewPortData:

        map_level_contents: MapLevelContents = self.map_cache_service.get_map_level_contents(
            location_index,
            level_index
        )

        u5_map: U5Map = self.global_registry.maps.get(location_index)
        map_level: U5MapLevel = u5_map.get_map_level(level_index)

        npcs = self.npc_service.get_npcs()
        assert len(npcs) > 0, "Must have at least 1 NPC (the player) to draw"

        def get_frame(world_coord: Coord[int]) -> Tile:
            
            if not map_level.get_size().is_in_bounds(world_coord):
                return self._default_tile
            
            npc: NpcAgent = npcs.get(world_coord, None)
            if not npc is None:
                return npc.current_tile

            interactable = self.global_registry.interactables.get(world_coord)
            if not interactable is None:
                return self.global_registry.tiles.get(interactable.get_current_tile_id())

            coord_contents = map_level_contents.get_coord_contents(world_coord)
            if coord_contents:
                return coord_contents.get_renderable_frame()
            return None
        
        return {
            world_coord:
            get_frame(world_coord)
            for world_coord in world_view_rect
        }
    
    def _get_lighting_map(self, world_view_rect: Rect[int]) -> set[Coord[int]]:

        party_location = self.party_agent.get_current_location()

        visible_coords: set[Coord[int]] = self.field_of_view_calculator.calculate_fov_visibility(
            fov_centre_location = party_location,
            view_rect           = world_view_rect
        )

        lit_coords = self.lighting_service.calculate_lighting(
            party_location,
            self.lighting_service.get_player_light_radius(),
            visible_coords
        )

        viewable_coords = visible_coords.intersection(lit_coords)

        return viewable_coords    
