# map_transitions.py
from typing import List, Tuple
from data import DataOVL
from location import load_location_map, metadata, location_names

Trigger = Tuple[int, int, int]  # (x, y, location_index)

def load_entry_triggers() -> List[Trigger]:
    """
    Load entry triggers from DATA.OVL and append the missing ones manually.
    Returns a list of (x, y, location_index).
    """
    dataOvl = DataOVL.load()

    xs = list(dataOvl.location_x_coords)
    ys = list(dataOvl.location_y_coords)

    # First 28 come straight from DATA.OVL
    triggers: List[Trigger] = [(x, y, i) for i, (x, y) in enumerate(zip(xs, ys))]

    # Append the 3 missing ones manually (coords TBD)
    triggers.extend([
        (0, 0, 27),  # LORD BRITISH'S CASTLE
        (0, 0, 28),  # BLACKTHORN'S CASTLE
        (0, 0, 29),  # SPEKTRAN
    ])

    return triggers


def spawn_from_trigger(location_index: int):
    """
    Load the map for the given location index, spawn player at middle-bottom
    of the map at the correct default z-level.
    """
    dataOvl = DataOVL.load()
    meta = metadata[location_index]
    u5map = load_location_map(location_index)

    # Start the player at the middle of the bottom of the screen.
    spawn_x = u5map.width // 2
    spawn_y = u5map.height - 2

    # Find this location's ordinal within its FILES group
    file_group = [m for m in metadata if m.files_index == meta.files_index]
    group_pos = next(i for i, m in enumerate(file_group) if m.name_index == location_index)

    if meta.files_index == 0:
        abs_level = dataOvl.map_index_towne[group_pos]
    elif meta.files_index == 1:
        abs_level = dataOvl.map_index_castle[group_pos]
    elif meta.files_index == 2:
        abs_level = dataOvl.map_index_keep[group_pos]
    elif meta.files_index == 3:
        abs_level = dataOvl.map_index_dwelling[group_pos]
    else:
        abs_level = 0

    # Convert absolute level index to relative index inside this map
    relative_level = abs_level - meta.map_index_offset
    if relative_level < 0 or relative_level >= len(u5map.levels):
        relative_level = 0  # safety fallback

    return u5map, spawn_x, spawn_y, relative_level
