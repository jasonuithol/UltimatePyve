from pathlib import Path
from typing import Callable, List, Tuple

from models.character_record import CharacterRecord

class SavedGameLoader:

    # Injectable
    saved_game: 'SavedGame'

    def _load(self, load_name: str, save_name: str):
        load_path = Path(f'u5/{load_name}.GAM')
        save_path = Path(f'u5/{save_name}.GAM')
        bytes = load_path.read_bytes()

        print(f"[game] Loaded {len(bytes)} from {save_path}")

        self.saved_game.init(bytes, save_path)

    def load_new(self, save_name="SAVE"):
        self._load(save_name, save_name)

    def load_existing(self, save_name="SAVE"):
        self._load("INIT", save_name)

class SavedGame:

    def init(self, raw: bytearray, save_path: Path):
        self.path = save_path
        self.raw = raw  # mutable buffer

        def field(offset: int, length: int) -> Tuple[Callable[[], bytes], Callable[[bytes], None]]:
            """Return getter/setter for a fixed-length field in the buffer."""
            def getter():
                return self.raw[offset:offset+length]
            def setter(value: bytes):
                if len(value) != length:
                    raise ValueError(f"Expected {length} bytes, got {len(value)}")
                self.raw[offset:offset+length] = value
            return getter, setter

        def field_u8(offset: int) -> Tuple[Callable[[], int], Callable[[int], None]]:
            """Return getter/setter for a single byte as int."""
            def getter():
                return self.raw[offset]
            def setter(value: int):
                if not (0 <= value <= 255):
                    raise ValueError("Byte value out of range")
                self.raw[offset] = value
            return getter, setter

        def field_u16(offset: int) -> Tuple[Callable[[], int], Callable[[int], None]]:
            """Return getter/setter for a 2-byte little-endian int."""
            def getter():
                return int.from_bytes(self.raw[offset:offset+2], 'little')
            def setter(value: int):
                self.raw[offset:offset+2] = value.to_bytes(2, 'little')
            return getter, setter

        # Character records
        self.characters: list[CharacterRecord] = []
        base = 0x0002
        for i in range(16):
            self.characters.append(CharacterRecord(self.raw, base + i * CharacterRecord.LENGTH))

        '''
        # --- Character records (16 × 32 bytes) ---
        self.character_records: List[Tuple[Callable[[], bytes], Callable[[bytes], None]]] = []
        base = 0x0002
        for i in range(16):
            self.character_records.append(field(base + i*32, 32))
        '''    

        # --- Party resources ---
        self.food = field_u16(0x0202)
        self.gold = field_u16(0x0204)
        self.keys = field_u8(0x0206)
        self.gems = field_u8(0x0207)
        self.torches = field_u8(0x0208)
        self.grapple = field_u8(0x0209)
        self.magic_carpets = field_u8(0x020A)
        self.skull_keys = field_u8(0x020B)
        self.last_day_minoc_skull_keys_taken = field_u8(0x020C)

        # --- Quest items / special flags ---
        self.amulet_lord_british = field_u8(0x020D)
        self.crown_lord_british = field_u8(0x020E)
        self.sceptre_lord_british = field_u8(0x020F)
        self.shard_falsehood = field_u8(0x0210)
        self.shard_hatred = field_u8(0x0211)
        self.shard_cowardice = field_u8(0x0212)
        self.unknown_213 = field_u8(0x0213)
        self.spy_glasses = field_u8(0x0214)
        self.hms_cape_plans = field_u8(0x0215)
        self.sextants = field_u8(0x0216)
        self.pocket_watch = field_u8(0x0217)
        self.black_badge = field_u8(0x0218)
        self.sandalwood_box = field_u8(0x0219)

        # --- Inventory items (IDs 0..111) ---
        self.inventory_items: List[Tuple[Callable[[], int], Callable[[int], None]]] = []
        base = 0x021A
        for item_id in range(112):
            self.inventory_items.append(field_u8(base + item_id))

        # --- Moonstones (8 slots each for X, Y, flags, Z) ---
        self.moonstone_x = [field_u8(0x028A + i) for i in range(8)]
        self.moonstone_y = [field_u8(0x0292 + i) for i in range(8)]
        self.moonstone_flags = [field_u8(0x029A + i) for i in range(8)]
        self.moonstone_z = [field_u8(0x02A2 + i) for i in range(8)]

        # --- Reagents (8 types) ---
        self.reagents = [field_u8(0x02AA + i) for i in range(8)]

        # --- Misc party state ---
        self.nightshade_mandrake_last_harvest_days = [field_u8(0x02B2 + i) for i in range(3)]
        self.party_member_count = field_u8(0x02B5)
        self.non_regenerating_object_flags = field(0x02B6, 0x0F)

        # --- Date/time ---
        self.current_year = field_u16(0x02CE)
        self.current_month = field_u8(0x02D7)
        self.current_day = field_u8(0x02D8)
        self.current_hour = field_u8(0x02D9)
        self.current_minute = field_u8(0x02DB)

        # --- Karma ---
        self.karma = field_u8(0x02E2)

        # --- Weather ---
        self.phase_of_trammel = field_u8(0x02DF)
        self.phase_of_felucca = field_u8(0x02E0)
        self.wind_direction = field_u8(0x02EC)

        # --- Party location ---
        self.party_location_index = field_u8(0x02ED)
        self.party_x = field_u8(0x02F0)
        self.party_y = field_u8(0x02F1)
        self.party_z = field_u8(0x02EF)

        # --- Light / vision ---
        self.current_light_intensity = field_u8(0x02FF)
        self.remaining_light_spell_duration = field_u8(0x0300)
        self.remaining_torch_duration = field_u8(0x0301)

        # --- Shadowlord locations ---
        self.shadowlord_falsehood_location = field_u8(0x0322)
        self.shadowlord_hatred_location = field_u8(0x0323)
        self.shadowlord_cowardice_location = field_u8(0x0324)

        # --- New block starting at 0x325 ---
        self.unknown_325 = field_u8(0x325)

        # Shrine quest bits
        self.ordained_shrine_quests = field_u8(0x326)  # bits 0–7
        self.unknown_327 = field_u8(0x327)
        self.completed_shrine_quests = field_u8(0x328)  # bits 0–7
        self.unknown_329 = field_u8(0x329)

        # Dungeon open/sealed flags (8 bytes)
        self.dungeon_open_flags = [field_u8(0x32A + i) for i in range(8)]

        # Shrine destroyed/ok flags (8 bytes)
        self.shrine_destroyed_flags = [field_u8(0x332 + i) for i in range(8)]

        # Dungeon room cleared flags (7 dungeons × 2 bytes)
        self.dungeon_room_cleared_flags = [field(0x33A + i*2, 2) for i in range(7)]

        # Annotations
        self.annotation_x_coords = [field_u8(0x348 + i) for i in range(0x20)]
        self.annotation_y_coords = [field_u8(0x368 + i) for i in range(0x20)]
        self.annotation_tiles = [field_u8(0x388 + i) for i in range(0x20)]
        self.annotation_count = field_u8(0x3A8)

        # Door state
        self.open_door_tile = field_u8(0x3A9)
        self.open_door_x = field_u8(0x3AA)
        self.open_door_y = field_u8(0x3AB)
        self.open_door_turns_remaining = field_u8(0x3AC)

        # Purchased ship coords
        self.purchased_ship_x = field_u8(0x3AD)
        self.purchased_ship_y = field_u8(0x3AE)

        # Ship sail direction
        self.ship_direction = field_u8(0x3AF)

        # Prompt at end of turn
        self.prompt_end_of_turn = field_u8(0x3B0)

        # Drunken moves remaining
        self.drunken_moves_remaining = field_u8(0x3B1)

        self.unknown_3B2 = field_u8(0x3B2)
        self.unknown_3B3 = field_u8(0x3B3)

        # Dungeon map (0x200 bytes)
        self.dungeon_map = field(0x3B4, 0x200)

        # NPC killed flags (0x80 bytes)
        self.npc_killed_flags = field(0x5B4, 0x80)

        # NPC met flags (0x80 bytes)
        self.npc_met_flags = field(0x634, 0x80)

        # Monster table (0x100 bytes)
        self.monster_table = field(0x6B4, 0x100)

        self.unknown_7B4 = field(0x7B4, 4)

        # NPC schedules (0x200 bytes)
        self.npc_schedules = field(0x7B8, 0x200)

        # Character/monster states (0x200 bytes)
        self.character_monster_states = field(0x9B8, 0x200)

        # Movement list table (0x400 bytes)
        self.movement_list_table = field(0xBB8, 0x400)

        # Movement list pointers (0x40 bytes)
        self.movement_list_pointers = field(0xFB8, 0x40)

        # NPC types (0x20 bytes)
        self.npc_types = field(0xFF8, 0x20)

        self.unknown_1018 = field(0x1018, 0x44)
        self.unknown_105C = field_u8(0x105C)

        # Dungeon orientation
        self.dungeon_orientation = field_u8(0x105D)

        # Dungeon graphics type
        self.dungeon_graphics_type = field_u8(0x105E)

        # Ship/skiff purchase encoding
        self.ship_purchase_code = field_u8(0x105F)

    # --- Convenience API ---
    def get_character(self, idx: int) -> CharacterRecord:
        return self.characters[idx]

    def get_item_qty(self, item_id: int) -> int:
        return self.inventory_items[item_id][0]()

    def set_item_qty(self, item_id: int, qty: int):
        self.inventory_items[item_id][1](qty)

    def save(self, path: Path = None):
        """Write the current buffer back to file."""
        target = path or self.path
        target.write_bytes(self.raw)