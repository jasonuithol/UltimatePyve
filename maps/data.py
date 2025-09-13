# file: maps/data.py
from pathlib import Path

class DataOVL:
    """
    Container for all parsed DATA.OVL sections.
    Each attribute is a raw bytes slice from the file.
    """
    _instance = None  # class-level cache

    def __init__(self, path: Path):
        raw = path.read_bytes()
        def slice_at(offset, length):
            return raw[offset:offset+length]

        # ------------- thanks Co-pilot/ChatGpt4 --------------------

        # 0x00 0x18 Unknown
        self.unknown_00 = slice_at(0x00, 0x18)
        # 0x18 0x38 Licence for the MS-Runtime
        self.ms_runtime_license = slice_at(0x18, 0x38)
        # 0x52 0xa6 Armour strings (13 of them)
        self.armour_strings = slice_at(0x52, 0xa6)
        # 0xf8 0x81 Weapon strings (10 of them)
        self.weapon_strings = slice_at(0xf8, 0x81)
        # 0x179 0x5a Ring and amulet strings (5 of them)
        self.ring_amulet_strings = slice_at(0x179, 0x5a)
        # 0x1d3 0x158 Character type, monster names (44 of them)
        self.monster_names = slice_at(0x1d3, 0x158)
        # 0x32b 0x165 Character type, monster names in capital letters (44 of them)
        self.monster_names_caps = slice_at(0x32b, 0x165)
        # 0x490 0x33 Abbreviated scroll names
        self.scroll_names_abbrev = slice_at(0x490, 0x33)
        # 0x4c3 0x2b Item names (5 of them)
        self.item_names = slice_at(0x4c3, 0x2b)
        # 0x4ee 0x18 "(x" where x goes from 0 to 7
        self.paren_x_strings = slice_at(0x4ee, 0x18)
        # 0x506 0x28 Shard names (3 of them)
        self.shard_names = slice_at(0x506, 0x28)
        # 0x52f 0x43 Additional item names (6 of them)
        self.item_names_extra = slice_at(0x52f, 0x43)
        # 0x572 0x11a Shortened names (29 of them)
        self.shortened_names = slice_at(0x572, 0x11a)
        # 0x68c 0x30 Potion colors (8 of them)
        self.potion_colors = slice_at(0x68c, 0x30)
        # 0x6bc 0x4d Reagents (8 of them)
        self.reagents = slice_at(0x6bc, 0x4d)
        # 0x709 0x1bb Spell names
        self.spell_names = slice_at(0x709, 0x1bb)
        # 0x8c4 0x54 Character type and names (11 of them)
        self.character_names = slice_at(0x8c4, 0x54)
        # 0x918 0x29 Health text (5 of them)
        self.health_text = slice_at(0x918, 0x29)
        # 0x941 0x64 Spell runes (26 of them)
        self.spell_runes = slice_at(0x941, 0x64)
        # 0x9a5 0xa8 Words of power for each spell
        self.words_of_power = slice_at(0x9a5, 0xa8)
        # 0xa4d 0x111 City names (in caps) (26 of them)
        self.city_names_caps = slice_at(0xa4d, 0x111)
        # 0xb5e 0x3a Dungeon names (8 of them)
        self.dungeon_names = slice_at(0xb5e, 0x3a)
        # 0xb98 0x48 Virtue names (8 of them)
        self.virtue_names = slice_at(0xb98, 0x48)
        # 0xbe0 0x1e Virtue mantras (8 of them)
        self.virtue_mantras = slice_at(0xbe0, 0x1e)
        # 0xbfe 0x2fc Store names
        self.store_names = slice_at(0xbfe, 0x2fc)
        # 0xefa 0x152 Barkeeper names
        self.barkeeper_names = slice_at(0xefa, 0x152)
        # 0x104c 0x24e Compressed words used in conversation files
        self.compressed_words = slice_at(0x104c, 0x24e)
        # 0x129a 0x11c Filenames
        self.filenames = slice_at(0x129a, 0x11c)
        # 0x13b6 0x3a6 Unknown
        self.unknown_13b6 = slice_at(0x13b6, 0x3a6)
        # 0x160c 0x37 Armour, weapon and scroll Attack values
        self.attack_values = slice_at(0x160c, 0x37)
        # 0x1644 0x2f Armour and Weapon Defensive values
        self.defense_values = slice_at(0x1644, 0x2f)
        # 0x1674 0x37 Armour, weapon and scroll range values
        self.range_values = slice_at(0x1674, 0x37)
        # 0x175c 0xa9 Weapon strings (+0x10)
        self.weapon_strings_plus10 = slice_at(0x175c, 0xa9)
        # 0x1806 0x70 Armor index (+0x10)
        self.armor_index_plus10 = slice_at(0x1806, 0x70)
        # 0x187a 0x1ee Text index (+0x10)
        self.text_index_plus10 = slice_at(0x187a, 0x1ee)
        # 0x1e2a 0x8 Which Map index do we start in for TOWNE.DAT
        self.map_index_towne = slice_at(0x1e2a, 0x8)
        # 0x1e32 0x8 Which Map index do we start in for DWELLING.DAT
        self.map_index_dwelling = slice_at(0x1e32, 0x8)
        # 0x1e3a 0x8 Which Map index do we start in for CASTLE.DAT
        self.map_index_castle = slice_at(0x1e3a, 0x8)
        # 0x1e42 0x8 Which Map index do we start in for KEEP.DAT
        self.map_index_keep = slice_at(0x1e42, 0x8)
        # 0x1e4a 0x1a Name of cities index (13 shorts, +0x10)
        self.city_name_index = slice_at(0x1e4a, 0x1a)
        # 0x1e6e 0x2c Name of dwellings/castles/keeps/dungeons index (22 shorts, +0x10)
        self.dwelling_name_index = slice_at(0x1e6e, 0x2c)
        # 0x1e9a 0x28 X-coordinates to Towns, Dwellings, Castles, Keeps, Dungeons
        self.location_x_coords = slice_at(0x1e9a, 0x28)
        # 0x1ec2 0x28 Y-coordinates to Towns, Dwellings, Castles, Keeps, Dungeons
        self.location_y_coords = slice_at(0x1ec2, 0x28)
        # 0x1f5e 0x20 Virtue and mantra index (+0x10)
        self.virtue_mantra_index = slice_at(0x1f5e, 0x20)
        # 0x1f7e 0x33b Unknown
        self.unknown_1f7e = slice_at(0x1f7e, 0x33b)
        # 0x22da 0x12 Arms seller's name index
        self.arms_seller_name_index = slice_at(0x22da, 0x12)
        # 0x22ec 0x20c Unknown
        self.unknown_22ec = slice_at(0x22ec, 0x20c)
        # 0x24f8 0x13e Indexes to the dialog text (+0x10
        # 0x22da 0x12 Arms seller's name index
        self.arms_seller_name_index = slice_at(0x22da, 0x12)
        # 0x24f8 0x13e Indexes to the dialog text (+0x10) (see .TLK)
        self.dialog_text_indexes = slice_at(0x24f8, 0x13e)
        # 0x2636 0x2b .DAT file names (4 files)
        self.dat_file_names = slice_at(0x2636, 0x2b)
        # 0x2661 0x9 Unknown
        self.unknown_2661 = slice_at(0x2661, 0x9)
        # 0x266a 0x269 Text strings (some unknown in the middle)
        self.text_strings_mixed = slice_at(0x266a, 0x269)
        # 0x28d3 0x83 Unknown
        self.unknown_28d3 = slice_at(0x28d3, 0x83)
        # 0x23ea 0x09 Shoppe Keeper – Towne indexes that have a tavern
        self.shoppe_tavern_indexes = slice_at(0x23ea, 0x09)
        # 0x23fa 0x04 Shoppe Keeper – Towne indexes that sell horses
        self.shoppe_horse_indexes = slice_at(0x23fa, 0x04)
        # 0x240a 0x04 Shoppe Keeper – Towne indexes that sell ships
        self.shoppe_ship_indexes = slice_at(0x240a, 0x04)
        # 0x241a 0x05 Shoppe Keeper – Towne indexes that sell reagents
        self.shoppe_reagent_indexes = slice_at(0x241a, 0x05)
        # 0x242a 0x03 Shoppe Keeper – Towne indexes that sell provisions (Guild)
        self.shoppe_provision_indexes = slice_at(0x242a, 0x03)
        # 0x243a 0x07 Shoppe Keeper – Towne indexes that sell healing
        self.shoppe_healing_indexes = slice_at(0x243a, 0x07)
        # 0x244a 0x06 Shoppe Keeper – Towne indexes that have an inn
        self.shoppe_inn_indexes = slice_at(0x244a, 0x06)
        # 0x2df4 0x14d Unknown
        self.unknown_2df4 = slice_at(0x2df4, 0x14d)
        # 0x2f41 0x5b Initial string
        self.initial_string = slice_at(0x2f41, 0x5b)
        # 0x2f9d 0xa STORY.DAT string
        self.story_dat_string = slice_at(0x2f9d, 0xa)
        # 0x2fa7 0x175 Unknown
        self.unknown_2fa7 = slice_at(0x2fa7, 0x175)
        # 0x311c 0x76 Menu texts (6 texts)
        self.menu_texts = slice_at(0x311c, 0x76)
        # 0x3192 0x22 ibm.hcs, rune.hcs, ibm.ch, runes.ch strings
        self.hcs_ch_strings = slice_at(0x3192, 0x22)
        # 0x31b4 0x42 Random texts
        self.random_texts_31b4 = slice_at(0x31b4, 0x42)
        # 0x31f6 0xa SAVED.GAM string
        self.saved_gam_string = slice_at(0x31f6, 0xa)
        # 0x3202 0x462 Random texts
        self.random_texts_3202 = slice_at(0x3202, 0x462)
        # 0x3664 0x2a Unknown
        self.unknown_3664 = slice_at(0x3664, 0x2a)
        # 0x3683 0x100 Bitmap of which of the first 256 tiles an NPC will walk on
        self.npc_walkable_bitmap = slice_at(0x3683, 0x100)
        # 0x3783 0x103 Unknown
        self.unknown_3783 = slice_at(0x3783, 0x103)
        # 0x3886 0x100 Chunking information for Britannia's map
        self.britannia_chunking_info = slice_at(0x3886, 0x100)
        # 0x3986 0xaf Random filenames, texts and unknown
        self.random_filenames_texts = slice_at(0x3986, 0xaf)
        # 0x3a35 0xd Unknown
        self.unknown_3a35 = slice_at(0x3a35, 0xd)
        # 0x3a42 0x28 Reagent base prices (towne by towne)
        self.reagent_base_prices = slice_at(0x3a42, 0x28)
        # 0x3a6a 0x28 Reagent quantities (towne by towne)
        self.reagent_quantities = slice_at(0x3a6a, 0x28)
        # 0x3a92 0x60 Armour/Weapons/Rings base prices
        self.base_prices_awr = slice_at(0x3a92, 0x60)
        # 0x3af2 0x48 Weapons sold by merchants in cities
        self.merchant_weapon_lists = slice_at(0x3af2, 0x48)
        # 0x3b3a 0x38 Unknown
        self.unknown_3b3a = slice_at(0x3b3a, 0x38)
        # 0x3b72 0x8 Innkeeper welcome text index into SHOPPE.DAT
        self.innkeeper_welcome_index = slice_at(0x3b72, 0x8)
        # 0x41e4 0x8c1 Random texts
        self.random_texts_41e4 = slice_at(0x41e4, 0x8c1)
        # 0x4aa5 0x2f2 Unknown
        self.unknown_4aa5 = slice_at(0x4aa5, 0x2f2)
        # 0x4d97 0x361 Random texts
        self.random_texts_4d97 = slice_at(0x4d97, 0x361)
        # 0x4e7e 0xc Inn room description text
        self.inn_room_description = slice_at(0x4e7e, 0xc)
        # 0x4e8a 0x5 Inn bed X-coordinate
        self.inn_bed_x_coords = slice_at(0x4e8a, 0x5)
        # 0x4e90 0x5 Inn bed Y-coordinate
        self.inn_bed_y_coords = slice_at(0x4e90, 0x5)

        # --------- thanks Meta/Llama ------------------------

        # 0x154C 0x30*2 Monster flags
        self.monster_flags = slice_at(0x154C, 0x30*2)

        # 0x1EEA 28*2 Moon phases
        self.moon_phases = slice_at(0x1EEA, 28*2)

        # 0x1F7E 8 Shrine x coordinates
        self.shrine_x_coords = slice_at(0x1F7E, 8)
        # 0x1F86 8 Shrine y coordinates
        self.shrine_y_coords = slice_at(0x1F86, 8)

        # 0x3E88 0x72 Hidden object tile indices
        self.hidden_object_tiles = slice_at(0x3E88, 0x72)
        # 0x3EFA 0x72 Hidden object qualities
        self.hidden_object_qualities = slice_at(0x3EFA, 0x72)
        # 0x3F6C 0x72 Hidden object location numbers
        self.hidden_object_locations = slice_at(0x3F6C, 0x72)
        # 0x3FDE 0x72 Hidden object z coordinates
        self.hidden_object_z_coords = slice_at(0x3FDE, 0x72)
        # 0x4050 0x72 Hidden object x coordinates
        self.hidden_object_x_coords = slice_at(0x4050, 0x72)
        # 0x40C2 0x72 Hidden object y coordinates
        self.hidden_object_y_coords = slice_at(0x40C2, 0x72)

        # 0x4513 0x8 Dungeon sprite indexes
        self.dungeon_sprite_indexes = slice_at(0x4513, 0x8)

        # 0x4D86 0x4 Dock x coordinates
        self.dock_x_coords = slice_at(0x4D86, 0x4)
        # 0x4D8A 0x4 Dock y coordinates
        self.dock_y_coords = slice_at(0x4D8A, 0x4)

        # 0x541E 8 Scan codes
        self.scan_codes = slice_at(0x541E, 8)
        # 0x5426 8 Internal codes
        self.internal_codes = slice_at(0x5426, 8)

        # 0x7252 0x32 Wishing well horse keywords
        self.wishing_well_horse_keywords = slice_at(0x7252, 0x32)

    @classmethod
    def load(cls):
        """
        Factory method: returns the singleton instance,
        creating it if it doesn't exist yet.
        """
        if cls._instance is None:
            cls._instance = cls(Path("u5/DATA.OVL"))
        return cls._instance

if __name__ == "__main__":

    def to_ascii(b: bytes) -> str:
        return ''.join(chr(c) if 32 <= c < 127 else '.' for c in b)

    def to_hex(b: bytes) -> str:
        return ' '.join(f"{c:02X}" for c in b)

    data = DataOVL.load()
    print(data)  # shows the repr summary

    for name, value in vars(data).items():
        ascii_str = to_ascii(value)
        hex_str = to_hex(value)
        print(f"\n{name}:")
        # ASCII: 40 chars per line
        ascii_lines = [ascii_str[i:i+40] for i in range(0, len(ascii_str), 40)]
        # HEX: 40 bytes * 3 chars ("AA ") = 120 chars per line
        hex_lines = [
            hex_str[i:i+120].rstrip()  # strip trailing space
            for i in range(0, len(hex_str), 120)
        ]
        max_lines = max(len(ascii_lines), len(hex_lines))
        ascii_lines.extend([''] * (max_lines - len(ascii_lines)))
        hex_lines.extend([''] * (max_lines - len(hex_lines)))
        for a_line, h_line in zip(ascii_lines, hex_lines):
            print(f"{a_line:<40}   {h_line}")

