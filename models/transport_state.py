from dark_libraries.dark_math    import Vector2
from models.enums.direction_map  import DirectionVector
from models.enums.transport_mode import TRANSPORT_DIRECTIONALITY_MAP, PlayerTransportTileId, TransportDirection, TransportDirectionality, TransportMode

class TransportState:

    def __init__(

            self, 
            transport_mode:        TransportMode, 
            untransported_tile_id: int, 

            last_east_west = TransportDirection.EAST, 
            last_nesw      = TransportDirection.EAST
    ):

        assert isinstance(untransported_tile_id, int), f"untransported_tile_id must be an int, not {untransported_tile_id.__class__.__name__}"

        self.transport_mode        = transport_mode
        self.untransported_tile_id = untransported_tile_id

        self.last_east_west = last_east_west
        self.last_nesw      = last_nesw

        self.__slots__ = ()

    def apply_move_offset(self, last_move_offset: Vector2[int]):

        direction_vector    = DirectionVector(last_move_offset)
        transport_direction = TransportDirection[direction_vector.name]

        self.last_nesw = transport_direction

        if transport_direction in [TransportDirection.EAST, TransportDirection.WEST]:
            self.last_east_west = transport_direction

    def is_transported(self) -> bool:
        return self.transport_mode != TransportMode.WALK

    def get_transport_tile_id(self) -> int:

        if self.transport_mode == TransportMode.WALK:
            return self.untransported_tile_id

        transport_directionality = TRANSPORT_DIRECTIONALITY_MAP[self.transport_mode]

        if transport_directionality == TransportDirectionality.EastWest:
            direction_name = self.last_east_west.name
        elif transport_directionality == TransportDirectionality.NorthEastSouthWest:
            direction_name = self.last_nesw.name
        else:
            assert False
            
        transport_tile_name = self.transport_mode.name + "_" + direction_name
        tile_id_enum = PlayerTransportTileId[transport_tile_name]

        assert tile_id_enum, f"Could not find PlayerTransportTileId[{transport_tile_name}]"

        return tile_id_enum.value
    
    def __str__(self):
        return (
            f"{self.__class__.__name__}: "
            +
            f"transport_mode={self.transport_mode}, "
            +
            f"untransported_tile_id={self.untransported_tile_id}, "
            +
            f"last_east_west={self.last_east_west}, " 
            +
            f"last_nesw={self.last_nesw}"
        )
