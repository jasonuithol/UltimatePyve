class LocationMetadata(tuple):
    __slots__ = ()

    def __new__(
        cls,
        location_index: int,             # index of the location for things like WorldLootLoader, and GlobalLocation references.
        name: str,                       # name of the location
        name_index: int,                 # which name the location takes.
        files_index: int,                # which file the location is in
        group_index: int,                # order of appearance of the town in the file. Use for indexing into DATA.OVL properties.
        map_index_offset: int,           # how many levels to skip to start reading the first level of the location.
        num_levels: int,                 # how many levels the location contains
        default_level: int,              # which level the player spawns in when entering the location.
        trigger_index: int,              # the index the entry triggers for this location are at.
        sound_track: str,                # an absolute path to the soundtrack
    ):
        return super().__new__(cls, (
            location_index,
            name,
            name_index,
            files_index,
            group_index,
            map_index_offset,
            num_levels,
            default_level,
            trigger_index,
            sound_track,
        ))

    @property
    def location_index(self) -> int:
        return self[0]

    @property
    def name(self) -> str:
        return self[1]

    @property
    def name_index(self) -> int:
        return self[2]

    @property
    def files_index(self) -> int:
        return self[3]

    @property
    def group_index(self) -> int:
        return self[4]

    @property
    def map_index_offset(self) -> int:
        return self[5]

    @property
    def num_levels(self) -> int:
        return self[6]

    @property
    def default_level(self) -> int:
        return self[7]

    @property
    def trigger_index(self) -> int:
        return self[8]

    @property
    def sound_track(self) -> str:
        return self[9]