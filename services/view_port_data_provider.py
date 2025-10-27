from dark_libraries.dark_math import Coord

from data.global_registry import GlobalRegistry

from models.agents.npc_agent import NpcAgent
from models.agents.party_agent import PartyAgent
from models.tile import Tile

from services.field_of_view_calculator import FieldOfViewCalculator
from services.lighting_service import LightingService
from services.map_cache.map_cache_service import MapCacheService
from services.map_cache.map_level_contents import MapLevelContents
from services.npc_service import NpcService

from view.view_port import ViewPort

ViewPortData = dict[Coord[int], Tile]

class ViewPortDataProvider:

    party_agent:              PartyAgent
    global_registry:          GlobalRegistry
    map_cache_service:        MapCacheService    
    field_of_view_calculator: FieldOfViewCalculator
    view_port:                ViewPort
    lighting_service:         LightingService
    npc_service:              NpcService

    def get_party_map_data(self)-> ViewPortData:

        player_location = self.party_agent.get_current_location()

        map_level_contents: MapLevelContents = self.map_cache_service.get_map_level_contents(
            player_location.location_index,
            player_location.level_index
        )

        visible_coords = self.field_of_view_calculator.calculate_fov_visibility(
            player_location,
            self.view_port.view_rect
        )

        lit_coords = self.lighting_service.calculate_lighting(
            player_location,
            self.lighting_service.get_player_light_radius(),
            visible_coords
        )

        npcs = self.npc_service.get_npcs()
        assert len(npcs) > 0, "Must have at least 1 NPC (the player) to draw"

        def get_frame(world_coord: Coord[int]) -> Tile:
            if not world_coord in visible_coords.intersection(lit_coords):
                return None
            npc: NpcAgent = npcs.get(world_coord, None)
            if not npc is None:
                return npc.current_tile
            interactable = self.global_registry.interactables.get(world_coord)
            if not interactable is None:
                return self.global_registry.tiles.get(interactable.get_current_tile_id())
            return map_level_contents.get_coord_contents(world_coord).get_renderable_frame()
        
        return {
            world_coord:
            get_frame(world_coord)
            for world_coord in self.view_port.view_rect
        }
