import pygame

from pathlib import Path
from typing import Any, Callable, Iterable

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.tile import Tile

MODS_DIR = Path("mods")

class ModdingService(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def _find_mod_files(self, section_path: str) -> Iterable[Path]:
        if not MODS_DIR.exists():
            return
        for specific_mod_dir in MODS_DIR.iterdir():
            if not specific_mod_dir.is_dir():
                continue
            content_dir = specific_mod_dir.joinpath(section_path)
            if content_dir.exists():
                for content_file in content_dir.iterdir():
                    if content_file.is_dir():
                        continue
                    self.log(f"({specific_mod_dir.name}) Found {section_path} mod file: {content_file}")
                    yield content_file

    def _load_mod_files(self, section_path: str, loader: Callable) -> Iterable[tuple[int,Any]]:
        for mod_file in self._find_mod_files(section_path):
            mod_thing_id = int(mod_file.stem)
            mod_thing = loader(mod_file.resolve())
            yield mod_thing_id, mod_thing
        
    def load_modded_tiles(self):
        modded_tiles = self._load_mod_files("tiles", lambda path: pygame.image.load(path))
        for tile_id, tile_surface in modded_tiles:
            registered_tile: Tile = self.global_registry.tiles.get(tile_id)  
            registered_tile.surface = tile_surface
                    
    def load_modded_location_soundtracks(self):
        modded_soundtracks = self._load_mod_files("music/locations", lambda path: path.resolve())
        for location_index, soundtrack_path in modded_soundtracks:
            self.global_registry.location_soundtracks.register_modded_content(location_index, soundtrack_path)

    def load_modded_transport_soundtracks(self):
        modded_soundtracks = self._load_mod_files("music/transport", lambda path: path.resolve())
        for transport_mode_index, soundtrack_path in modded_soundtracks:
            self.global_registry.transport_soundtracks.register_modded_content(transport_mode_index, soundtrack_path)

    #
    # TODO: Load mods IMMEDIATELY after loading the OG resources, not all at the end.
    #       It will then be impossible (theoretically) for downstream resources that cache other upstream resources to get out-of-sync with modded content. 
    #
    def load_mods(self):

        self.log("DEPRECATED: ModdingService.load_mods() is scheduled for destruction.")

        self.load_modded_tiles()
        self.load_modded_location_soundtracks()
        self.load_modded_transport_soundtracks()

        self.log("All mods loaded.")



