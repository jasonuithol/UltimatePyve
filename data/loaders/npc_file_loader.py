from pathlib import Path
from typing  import Iterable

from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry
from models.location_metadata import LocationMetadata
from models.npc_file import NpcFile


class NpcFileLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    FILES = (
        "TOWNE.NPC",
        "DWELLING.NPC",
        "CASTLE.NPC",
        "KEEP.NPC",
    )

    def load(self, u5_path: Path, metadata: Iterable[LocationMetadata]):
        parsed: dict[int, NpcFile] = {}
        for files_index, filename in enumerate(__class__.FILES):
            path = u5_path / filename
            if not path.exists():
                self.log(f"WARN: {filename} not found at {path}")
                continue
            parsed[files_index] = NpcFile(path)
            self.log(f"DEBUG: Loaded {filename}")

        registered = 0
        for meta in metadata:
            if meta.files_index is None:
                continue
            npc_file = parsed.get(meta.files_index)
            if npc_file is None:
                continue
            section = npc_file.maps[meta.group_index]
            self.global_registry.npc_sections.register(meta.location_index, section)
            registered += 1

        self.log(f"Registered {registered} NPC map sections.")
