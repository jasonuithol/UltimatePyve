from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.data_ovl import DataOVL

class SpellRuneLoader(LoggerMixin):
    
    data_ovl:        DataOVL
    global_registry: GlobalRegistry

    def load(self):
        for rune in DataOVL.to_strs(self.data_ovl.spell_runes):
            if len(rune) == 0:
                continue
            self.global_registry.runes.register(rune[0].lower(), rune)
        self.log(f"Registered {len(self.global_registry.runes)} spell runes.")