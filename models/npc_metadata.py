from models.enums.terrain_category import TerrainCategory

class NpcAbilitiesAttack:

    # Abilities: Attack
    ranged_weapon_glyphcode: int = None
    has_bludgeoning_attack:  bool = False

    magic_missile: bool = False
    poison_melee:  bool = False
    poison_spit:   bool = False
    steals_food:   bool = False

class NpcAbilitiesMagic:

    # Abilities: Magic
    can_teleport:         bool = False
    can_become_invisible: bool = False
    can_summon_a_daemon:  bool = False
    can_charm:            bool = False

class NpcAbilitiesDefence:

    # Abilities: Defence
    never_takes_damage:  bool = False
    can_split_in_two:    bool = False
    is_undead:           bool = False
    leaves_no_corpse:    bool = False

class NpcAbilitiesTerrain:

    # Abilities: Spawning
    ambushes_campers: bool = False

    # map types
    common_in_dungeons: bool = False
    overworld:          bool = False
    underworld:         bool = False

    # terrain types
    allowed_terrain_spawns = set[TerrainCategory]()
    allowed_terrain_travel = set[TerrainCategory]()

class NpcMetadata:

    def __init__(
        self, 
        name: str,
        npc_tile_id: int,

        general_stats = tuple[int,int,int],  # STR,DEX,INT
        combat_stats  = tuple[int,int,int],  # armour, damage, hitpoints
        other_stats   = tuple[int,int,int]   # max_party_size, treasure_percent, experience_points
    ):
        self.name = name
        self.npc_tile_id = npc_tile_id

        self.strength      , self.dexterity       , self.intelligence      = general_stats
        self.armour        , self.damage          , self.hitpoints         = combat_stats
        self.max_party_size, self.treasure_percent, self.experience_points = other_stats

        self.abilities_attack    = NpcAbilitiesAttack()
        self.abilities_magic     = NpcAbilitiesMagic()
        self.abilities_defence   = NpcAbilitiesDefence()
        self.abilities_terrain   = NpcAbilitiesTerrain()
        

