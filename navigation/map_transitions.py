# map_transitions.py
from typing import Optional, Dict
from loaders.data import DataOVL
from dark_libraries.dark_math import Coord

Triggers = Dict[Coord, int]  # (x, y, location_index)

_triggers: Triggers = None

def load_entry_triggers() -> Triggers:
    """
    Loads 39 entry triggers from DATA.OVL
    Returns a list of (x, y, location_index).
    """
    global _triggers
    if _triggers is None:
        _triggers = {}
        dataOvl = DataOVL.load()

        xs = list(dataOvl.location_x_coords)
        ys = list(dataOvl.location_y_coords)

        for trigger_index, (x, y) in enumerate(zip(xs, ys)):
            _triggers[Coord(x,y)] = trigger_index
    return _triggers

def get_entry_trigger(coord: Coord) -> Optional[int]:
    return load_entry_triggers().get(coord, None)

if __name__ == "__main__":
    print(f"entry trigger for 0,0: {get_entry_trigger(Coord(0,0))}")
    print(f"entry trigger for Iolo's Hut: {get_entry_trigger(Coord(45,62))}")
