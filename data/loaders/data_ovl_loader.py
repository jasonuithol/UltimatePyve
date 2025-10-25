from pathlib import Path
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.data_ovl import DataOVL


class DataOVLLoader(LoggerMixin):

    global_registry: GlobalRegistry

    def load(self, u5_path: Path):
        self.global_registry.data_ovl = DataOVL(u5_path)
        self.log("Loaded DATA.OVL")
    