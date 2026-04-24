from pathlib import Path
from typing  import Iterable

from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry
from models.location_metadata import LocationMetadata
from models.tlk_file import CompressedWords, NpcDialog, TlkFile


class TlkFileLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    FILES = (
        "TOWNE.TLK",
        "DWELLING.TLK",
        "CASTLE.TLK",
        "KEEP.TLK",
    )

    def load(self, u5_path: Path, metadata: Iterable[LocationMetadata]):
        compressed_words = CompressedWords(self.global_registry.data_ovl.compressed_words)

        parsed: dict[int, TlkFile] = {}
        for files_index, filename in enumerate(__class__.FILES):
            path = u5_path / filename
            if not path.exists():
                self.log(f"WARN: {filename} not found at {path}")
                continue
            parsed[files_index] = TlkFile(path, compressed_words)
            self.log(f"DEBUG: Loaded {filename}")

        registered = 0
        for meta in metadata:
            if meta.files_index is None:
                continue
            tlk = parsed.get(meta.files_index)
            if tlk is None:
                continue
            npc_section = self.global_registry.npc_sections.get(meta.location_index)
            if npc_section is None:
                continue

            dialogs: dict[int, NpcDialog] = {}
            for dialog_number in npc_section.dialog_numbers:
                if dialog_number == 0 or dialog_number in dialogs:
                    continue
                dialog = tlk.dialogs.get(dialog_number)
                if dialog is None:
                    continue
                dialogs[dialog_number] = dialog

            if dialogs:
                self.global_registry.npc_dialogs.register(meta.location_index, dialogs)
                registered += 1

        self.log(f"Registered NPC dialogs for {registered} locations.")
