from enum import Enum

class HitPointLevel(Enum):
    FULL_HEALTH        = 99
    LIGHTLY_INJURED    = 80
    HEAVILY_INJURED    = 50
    CRITICALLY_INJURED = 25

HIT_POINT_DICTIONARY = {
    (0.81, 1.00) : "Full Health",
    (0.51, 0.80) : "Lightly Wounded",
    (0.26, 0.50) : "Heavily Wounded",
    (0.01, 0.25) : "Critically Wounded",
    (0.00, 0.00) : "Killed"
}

def get_hp_level_text(hp_percentage: float) -> str:
    for hp_range, description in HIT_POINT_DICTIONARY.items():
        if hp_range[0] <= hp_percentage <= hp_range[1]:
            return description
    assert False, f"Should never arrive here: hp_percentage={hp_percentage}"
    