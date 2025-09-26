from .terrain import Terrain
from .terrain_registry import TerrainRegistry

class TerrainFactory:

    # Injectable
    terrain_registry: TerrainRegistry

    def _build_terrains(self) -> list[Terrain]:
                
        # make a list of the 256 terrains all set to false.
        terrains: list[Terrain] = list(map(lambda _: Terrain(), range(256)))
        
        # walkable terain
        for start, finish in [
            (  4, 11),
            ( 14, 38), # INCLUDES BRIDGE
            ( 44, 45),
            ( 48, 55),
            ( 57, 64),
            ( 68, 69),
            ( 71, 73),
            (106,107), # BRIDGES
            (134,135), # A grate you can Klimb down, and an arch you can walk under
            (140,140), # TRAPDOOR
            (143,147), # INCLUDES LAVA AND CHAIRS
            (170,172), # includes BEDS
            (196,201), # ladders and stairs
            (220,221), # includes moongate
            (227,231),
            (255,255), # the void ????
        ]:
            for i in range(start, finish + 1):
                terrains[i].walk = True
                terrains[i].horse = True
                terrains[i].carpet = True

        # horse refusals
        for i in [
            4,      # swamp
            12,      # mountains
            143,      # lava
        ]:
            terrains[i].horse = False
                
        # horse and carpet refusal
        for start, finish in [
            (144,147),     # chairs
            (171,172),      # bed
            (196,199),      # stairs
            (200,201)      # ladders      
        ]:
            for i in range(start, finish + 1):
                terrains[i].horse = False
                terrains[i].carpet = False
                
        # carpet traversable extras
        for start, finish in [
            (  1,  3), # water (includes ocean)
            ( 96,105), # river
            (108,111), # river heads
        ]:
            for i in range(start, finish + 1):
                terrains[i].carpet = True

        # skiff traversable
        for start, finish in [
            (  1,  3), # water (includes ocean)
            ( 52, 55), # angled beach
            ( 96,105), # river
            (108,111), # river heads
        ]:
            for i in range(start, finish + 1):
                terrains[i].skiff = True

        # ship and sail traversable
        for i in [1,  2]:
            terrains[i].ship = True
            terrains[i].sail = True

        # Ladders
        terrains[200].move_up = True
        terrains[201].move_down = True

        # Stairs
        for i in [196, 197, 198, 199]:
            terrains[i].stairs = True

        # climbable - only when on foot
        for i in [
            76,     # rock pile
            202,    # fence east-west
            203     # fence north-south
        ]:
            terrains[i].climb = True

        # Grapple Hook
        terrains[12].grapple = True

        # Light emitters
        for i in [176, 177, 178, 179, 188, 189, 190, 191]:
            terrains[i].emits_light = True

        # Light blockers
        for i in [
            10,     # deep forest
            13,     # mountain peak
            74,     # wall with arrow slot  [WINDOWED]
            75,     # wall with grate       [WINDOWED]
            78,     # wall with secret door
            79,     # wall
            90,     # pantry
            151,    # door, magic
            152,    # door, magic, windowed [WINDOWED]
            184,    # door
            185,    # door (locked)
            186,    # door with window      [WINDOWED]
            187,    # door locked, window   [WINDOWED]
            248    # wall with billboard
        ]:
            terrains[i].blocks_light = True

        # Windowed (blocks light unless avatar standing right next to tile)
        for i in [
            74,     # wall with arrow slot  [WINDOWED]
            75,     # wall with grate       [WINDOWED]
            152,    # door, magic, windowed [WINDOWED]
            186,    # door with window      [WINDOWED]
            187     # door locked, window   [WINDOWED]
        ]:
            terrains[i].windowed = True

        return terrains

    def register_terrains(self):
        terrains = self._build_terrains()
        for tile_id, terrain in enumerate(terrains):
            self.terrain_registry.register_terrain(tile_id, terrain)