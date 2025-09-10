from dataclasses import dataclass
from enum import Enum
from dark_libraries.custom_decorators import auto_init
from loaders import DataOVL

class Slot(Enum):
    HEAD = 0
    BODY = 1
    NECK = 2
    FINGER = 3
    ONE_HAND = 4
    TWO_HAND = 5

class TileId(Enum):
    WEAPON = 261
    SHIELD = 262
    HELM = 265
    RING = 266
    ARMOUR = 267
    AMULET = 268

class RuneId(Enum):
    HELM = 1
    SHIELD = 2
    ARMOR = 3
    DAGGER = 4
    SLING = 5
    CLUB = 6
    FLAMING_OIL = 7
    ARROW_AMMUNITION = 8
    THROWING_AXE = 9
    # missing 10
    SWORD = 11
    MACE = 12
    # missing 13
    SUN_SYMBOL = 14        # uncertain
    BOW = 15
    CROSSBOW = 16
    TWO_HANDED_HAMMER = 17
    TWO_HANDED_AXE = 18
    GLASS_SWORD = 19       # maybe
    HALBERD = 20
    JEWELED_SWORD = 21
    MAGIC_BOW = 22
    MAGIC_AXE = 23
    RING = 24
    AMULET = 25
    SPIKED_COLLAR = 26
    ANKH = 27
    SCROLL = 28
    POTION = 29
    MORNING_STAR = 30


@dataclass
class EquipableItem:
    name: str
    short_name: str
    range_: int
    defence: int
    attack: int
    slot: Slot
    tile_id: TileId
    rune_id: RuneId

def to_ints(bytes: bytearray):
    return list(map(lambda byte: int(byte), bytes))

def to_strs(bytes: bytearray):
    return bytes.split(b"\0")

class EquipableItemFactory:

    # Injectable
    dataOvl: DataOVL

        
    def build(self):

        mysterious_indexes_armour = to_ints(dataOvl.armor_index_plus10)
    
        descriptions_armour = to_strs(dataOvl.armour_strings)
        descriptions_weapons = to_strs(dataOvl.weapon_strings)
        descriptions_weapons_plus10 = to_strs(dataOvl.weapon_strings_plus10)
        descriptions_rings_amulets = to_strs(dataOvl.ring_amulet_strings)
    
        descriptions = [
            descriptions_armour,
            descriptions_weapons,
            descriptions_weapons_plus10,
            descriptions_rings_amulets
        ]

        shortened_names = to_strs(dataOvl.shortened_names)

        defence_values = to_ints(dataOvl.defense_values)
        range_values = to_ints(dataOvl.range_values)
        attack_values = to_ints(dataOvl.attack_values)        

        items = []

        def build_armour(description_index: int, short_index: int, dra_values_index: int, slot: Slot, tile_id: TileId, rune_id: RuneId):
            item = EquipableItem(
                name = descriptions[description_index[0]][description_index[1]],
                short_name = None if short_index is None else shortened_names[short_index],
                range_ = range_values[dra_values_index],
                defence = defence_values[dra_values_index],
                attack = attack_values[dra_values_index],
                slot = slot,
                tile_id = tile_id,
                rune_id = rune_id
            )
            items.append(item)
            return item
        
        # Helms
        build_armour(  (0, 0),  0  ,  0, Slot.HEAD, TileId.HELM, RuneId.HELM)
        build_armour(  (2, 0), None,  1, Slot.HEAD, TileId.HELM, RuneId.HELM)
        build_armour(  (2, 1), None,  2, Slot.HEAD, TileId.HELM, RuneId.HELM)
        build_armour(  (0, 1),  1  ,  3, Slot.HEAD, TileId.HELM, RuneId.HELM)
        
        # Shields
        build_armour(  (0, 2),  2  ,  4, Slot.ONE_HAND, TileId.SHIELD, RuneId.SHIELD)
        build_armour(  (0, 3),  3  ,  5, Slot.ONE_HAND, TileId.SHIELD, RuneId.SHIELD)
        build_armour(  (0, 4),  4  ,  6, Slot.ONE_HAND, TileId.SHIELD, RuneId.SHIELD)
        build_armour(  (0, 5),  5  ,  7, Slot.ONE_HAND, TileId.SHIELD, RuneId.SHIELD)
        build_armour(  (0, 6),  6  ,  8, Slot.ONE_HAND, TileId.SHIELD, RuneId.SHIELD)

        # Armour
        build_armour(  (0, 7),  7  ,  9, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)
        build_armour(  (0, 8),  8  , 10, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)
        build_armour(  (2, 2), None, 11, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)
        build_armour(  (0, 9),  9  , 12, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)
        build_armour(  (0,10), 10  , 13, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)

        # Plate and mystic armour, TODO
        #build_armour(  (0, 2), 2   , 4, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)
        #build_armour(  (0, 2), 2   , 4, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)

        for item in items:
            print(item)

#
# MAIN
#
if __name__ == "__main__":

    dataOvl = DataOVL.load()

    factory = EquipableItemFactory()
    factory.dataOvl = dataOvl

    factory.build()




