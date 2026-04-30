from pathlib import Path

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.shoppe_strings import ShoppeStrings


class ShoppeDatLoader(LoggerMixin):

    global_registry: GlobalRegistry

    def load(self, u5_path: Path):
        strings = ShoppeStrings.from_path(u5_path, self.global_registry.data_ovl)
        self.global_registry.shoppe_strings = strings
        self.log(f"Loaded {len(strings)} SHOPPE.DAT strings")
