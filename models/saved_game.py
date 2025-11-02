from datetime import datetime
from pathlib import Path

from dark_libraries.dark_math import Coord
from models.character_record import CharacterRecord
from models.enums.inventory_offset import InventoryOffset
from models.global_location import GlobalLocation

class SavedGame:

    def __init__(self, raw: bytearray, save_path: Path):
        self.path = save_path
        self.raw = raw  # mutable buffer

    def read_u8(self, offset: int) -> int:
        if isinstance(offset, InventoryOffset):
            offset = offset.value
        return self.raw[offset]

    def write_u8(self, offset: int, value: int):
        assert value < 256, f"Cannot write value {value} to u8 storage"
        if isinstance(offset, InventoryOffset):
            offset = offset.value
        self.raw[offset] = value

    def read_u16(self, offset: int) -> int:
        return int.from_bytes(self.raw[offset : offset + 2], 'little')

    def write_u16(self, offset: int, value: int):
        assert value < 65536, f"Cannot write value {value} to u16 storage"
        self.raw[offset:offset+2] = value.to_bytes(2, 'little')

    def create_character_record(self, character_record_index: int) -> CharacterRecord:
        assert character_record_index < 16, f"Expected index < 16, got {character_record_index}"
        offset = 0x0002 + character_record_index * 32
        return CharacterRecord(self.raw, offset)

    def read_party_member_count(self) -> int:
        return self.read_u8(0x02B5)

    def write_party_member_count(self, value: int) -> int:
        return self.write_u8(0x02B5, value)

    def read_party_location(self) -> GlobalLocation:
        return GlobalLocation(
            location_index = self.read_u8(0x02ED),
            level_index    = self.read_u8(0x02EF),
            coord          = Coord[int](self.read_u8(0x02F0), self.read_u8(0x02F1))
        )

    def write_party_location(self, party_location: GlobalLocation):
        self.write_u8(0x02ED ,party_location.location_index)
        self.write_u8(0x02EF ,party_location.level_index)
        x, y = party_location.coord
        self.write_u8(0x02F0, x)
        self.write_u8(0x02F1, y)

    def read_current_datetime(self) -> datetime:
        return datetime(
            year   = self.read_u8(0x02CE), 
            month  = self.read_u8(0x02D7), 
            day    = self.read_u8(0x02D8), 
            hour   = self.read_u8(0x02D9), 
            minute = self.read_u8(0x02DB)
        )
        
    def write_current_datetime(self, value: datetime):
        self.write_u8(0x02CE, value.year  ) 
        self.write_u8(0x02D7, value.month ) 
        self.write_u8(0x02D8, value.day   ) 
        self.write_u8(0x02D9, value.hour  ) 
        self.write_u8(0x02DB, value.minute)

    '''
    def read_equipable_item_quantity(self, dra_index: int) -> int:
        assert dra_index < 112, f"Expected index < 112, got {dra_index}"
        offset = 0x021A
        return self.read_u8(offset + dra_index)

    def write_equipable_item_quantity(self, dra_index: int, quantity: int):
        assert dra_index < 112, f"Expected index < 112, got {dra_index}"

        # It's recommended to read this in Shrek's voice, or Fat Bastard's.
        assert quantity < 100, "In this game, you cannae hold 100 or more things of the same type of thing (except gold and food, which need u16 stores, and are NOT EQUIPABLE ITEMS)"

        offset = 0x021A
        self.write_u8(offset + dra_index, quantity)

    '''



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
        self.amulet_of_lord_british = field_u8(0x020D)
        self.crown_of_lord_british = field_u8(0x020E)
        self.sceptre_of_lord_british = field_u8(0x020F)
        self.shard_of_falsehood = field_u8(0x0210)
        self.shard_of_hatred = field_u8(0x0211)
        self.shard_of_cowardice = field_u8(0x0212)
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
    '''
