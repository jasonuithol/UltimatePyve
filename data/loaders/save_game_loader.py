from pathlib import Path
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.saved_game import SavedGame

class SavedGameLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def _load(self, u5_path: Path, load_name: str, save_name: str) -> SavedGame:

        # Detect GOG cloud_save
        cloud_save = u5_path.joinpath("cloud_saves").joinpath(f"{load_name}.GAM")

        #
        # TODO: Remember this when saving a game.
        #
        if cloud_save.exists():
            load_path = cloud_save
        else:
            load_path = u5_path.joinpath(f"{load_name}.GAM")

        bytes = bytearray(load_path.read_bytes())
        self.log(f"Loaded {len(bytes)} bytes from {load_path}")

        #
        # TODO: this shit
        #
        save_path = None
        return SavedGame(bytes, save_path)

    def load_existing(self, u5_path: Path, save_name="SAVED") -> SavedGame:
        return self._load(u5_path, save_name, save_name)

    def load_new(self, u5_path: Path, save_name="SAVED") -> SavedGame:
        return self._load(u5_path, "INIT", save_name)

#
# MAIN
#
if __name__ == "__main__":
    import inspect

    loader = SavedGameLoader()
    loader.global_registry = GlobalRegistry()
    loader.load_existing()

    # An instance of SaveGame
    saved_game_instance = loader.global_registry.saved_game

    for name, val in vars(saved_game_instance).items():
        if isinstance(val, tuple) and len(val) == 2:
            getter, setter = val
            try:
                print(f"{name} = {getter()}")
            except Exception as e:
                print(f"ERROR: {name} raised {e}")

    for record_index, char_record in enumerate(saved_game_instance.characters):
        print(f"--------------------- CHARACTER RECORD[{record_index}] {char_record.name} -------------------------------")
        for name, value in inspect.getmembers(char_record.__class__, lambda o: isinstance(o, property)):
                print(f"{name} = {getattr(char_record, name)}")
            