# map_transitions.py
from typing import List, Tuple
from data import DataOVL
from location import load_location_map

Trigger = Tuple[int, int, int]  # (x, y, location_index)

def load_entry_triggers() -> List[Trigger]:
    """
    Load entry triggers from DATA.OVL and append the missing ones manually.
    Returns a list of (x, y, location_index).
    """
    dataOvl = DataOVL.load()

    xs = list(dataOvl.location_x_coords)
    ys = list(dataOvl.location_y_coords)

    # First 39 come straight from DATA.OVL
    triggers: List[Trigger] = [(x, y, i) for i, (x, y) in enumerate(zip(xs, ys))]
    return triggers

def spawn_from_trigger(trigger_index: int):
    """
    Load the map for the given location index, spawn player at middle-bottom
    of the map at the correct default z-level.
    """
    u5map = load_location_map(trigger_index)

    # Start the player at the middle of the bottom of the screen.
    spawn_x = u5map.width // 2 - 1
    spawn_y = u5map.height - 2

    default_level = u5map.location_metadata.default_level if u5map.location_metadata else 0
    return u5map, spawn_x, spawn_y, default_level
