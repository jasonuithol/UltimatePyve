import pygame
from dark_libraries import immutable, auto_init

@immutable
@auto_init
class LocationMetadata:
    location_index: int         # index of the location for things like WorldLootLoader, and GlobalLocation references.
    name: str                   # name of the location
    name_index: int             # which name the location takes.
    files_index: int            # which file the location is in
    group_index: int            # order of appearance of the town in the file. Use for indexing into DATA.OVL properties.
    map_index_offset: int       # how many levels to skip to start reading the first level of the location.
    num_levels: int             # how many levels the location contains
    default_level: int          # which level the player spawns in when entering the location.
    trigger_index: int          # the index the entry triggers for this location are at.
    sound_track: str            # an absolute path to the soundtrack