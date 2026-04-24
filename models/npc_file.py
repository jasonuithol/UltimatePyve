from dataclasses import dataclass
from pathlib import Path


_SCHEDULE_BYTES = 16
_NPCS_PER_MAP   = 32
_MAPS_PER_FILE  = 8
_MAP_BYTES      = _NPCS_PER_MAP * _SCHEDULE_BYTES + _NPCS_PER_MAP + _NPCS_PER_MAP  # 576
_FILE_BYTES     = _MAP_BYTES * _MAPS_PER_FILE                                      # 4608


@dataclass(frozen=True)
class NpcSchedule:
    ai_types: tuple[int, int, int]
    x_coords: tuple[int, int, int]
    y_coords: tuple[int, int, int]
    z_coords: tuple[int, int, int]
    times:    tuple[int, int, int, int]

    @classmethod
    def from_bytes(cls, b: bytes) -> "NpcSchedule":
        assert len(b) == _SCHEDULE_BYTES, f"expected {_SCHEDULE_BYTES} bytes, got {len(b)}"
        def signed(x: int) -> int:
            return x - 256 if x >= 128 else x
        return cls(
            ai_types = (b[0], b[1], b[2]),
            x_coords = (b[3], b[4], b[5]),
            y_coords = (b[6], b[7], b[8]),
            z_coords = (signed(b[9]), signed(b[10]), signed(b[11])),
            times    = (b[12], b[13], b[14], b[15]),
        )

    def is_empty(self) -> bool:
        return (
            self.ai_types == (0, 0, 0)
            and self.x_coords == (0, 0, 0)
            and self.y_coords == (0, 0, 0)
            and self.z_coords == (0, 0, 0)
            and self.times    == (0, 0, 0, 0)
        )

    def slot_for_hour(self, hour: int) -> int:
        # 4 transition times but only 3 position/AI slots: time index 3 wraps to slot 1.
        times = self.times
        if times == (0, 0, 0, 0):
            return 0

        def slot_of(time_index: int) -> int:
            return 1 if time_index == 3 else time_index

        for i in range(4):
            if times[i] == hour:
                return slot_of(i)

        t0, t1, t2, t3 = times
        if t3 < hour < t0: return 1
        if t0 < hour < t1: return 0
        if t1 < hour < t2: return 1
        if t2 < hour < t3: return 2

        earliest = min(range(4), key=lambda i: times[i])
        latest   = max(range(4), key=lambda i: times[i])
        prev_to_earliest = 1 if earliest == 0 else earliest - 1

        if hour < times[earliest]: return prev_to_earliest
        if hour > times[latest]:   return slot_of(latest)

        raise AssertionError(f"slot_for_hour fell through: hour={hour} times={times}")


@dataclass(frozen=True)
class NpcMapSection:
    schedules:      tuple[NpcSchedule, ...]    # 32 entries; slot 0 is unused
    types:          tuple[int, ...]            # 32 uint8 — NPC profession
    dialog_numbers: tuple[int, ...]            # 32 uint8 — 1..N indexes into the matching .TLK

    @classmethod
    def from_bytes(cls, b: bytes) -> "NpcMapSection":
        assert len(b) == _MAP_BYTES, f"expected {_MAP_BYTES} bytes, got {len(b)}"
        schedules = tuple(
            NpcSchedule.from_bytes(b[i * _SCHEDULE_BYTES : (i + 1) * _SCHEDULE_BYTES])
            for i in range(_NPCS_PER_MAP)
        )
        types_start  = _NPCS_PER_MAP * _SCHEDULE_BYTES     # 512
        dialog_start = types_start + _NPCS_PER_MAP         # 544
        types   = tuple(b[types_start  : types_start  + _NPCS_PER_MAP])
        dialogs = tuple(b[dialog_start : dialog_start + _NPCS_PER_MAP])
        return cls(schedules=schedules, types=types, dialog_numbers=dialogs)


class NpcFile:
    """
    Parses a U5 NPC file (TOWNE.NPC / DWELLING.NPC / CASTLE.NPC / KEEP.NPC).

    Layout: 8 map sections × 576 bytes. Each section holds 32 × 16-byte schedule
    records, followed by 32 uint8 types, then 32 uint8 dialog_numbers.
    Slot 0 in every section is unused (schedule zero-filled).
    """

    def __init__(self, path: Path):
        raw = Path(path).read_bytes()
        assert len(raw) == _FILE_BYTES, f"expected {_FILE_BYTES} bytes, got {len(raw)}"
        self.maps: tuple[NpcMapSection, ...] = tuple(
            NpcMapSection.from_bytes(raw[i * _MAP_BYTES : (i + 1) * _MAP_BYTES])
            for i in range(_MAPS_PER_FILE)
        )
