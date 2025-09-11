from dataclasses import dataclass
from enum import Enum

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

#        mysterious_indexes_armour = to_ints(dataOvl.armor_index_plus10)
    
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

        def build_item(description_index: tuple[int,int], short_index: int, dra_values_index: int, slot: Slot, tile_id: TileId, rune_id: RuneId):

            if dra_values_index is None:
                d,r,a = 0,0,0
            else:
                d,r,a = defence_values[dra_values_index], range_values[dra_values_index], attack_values[dra_values_index]

            item = EquipableItem(
                name = descriptions[description_index[0]][description_index[1]],
                short_name = None if short_index is None else shortened_names[short_index],
                range_ = r,
                defence = d,
                attack = a,
                slot = slot,
                tile_id = tile_id,
                rune_id = rune_id
            )
            items.append(item)
            return item
        
        def build_helm(description_index: tuple[int,int], short_index: int, dra_values_index: int):
            build_item(description_index, short_index, dra_values_index, Slot.HEAD, TileId.HELM, RuneId.HELM)

        # Helms
        build_helm((0, 0),    0, 0) # Leather Helm
        build_helm((2, 0), None, 1) # Chain Coif
        build_helm((2, 2), None, 2) # Iron Helm
        build_helm((0, 1),    1, 3) # Spiked Helm
        
        def build_shield(description_index: tuple[int,int], short_index: int, dra_values_index: int):
            build_item(description_index, short_index, dra_values_index, Slot.ONE_HAND, TileId.SHIELD, RuneId.SHIELD)

        # Shields
        build_shield((0, 2), 2, 4) # Small Shield
        build_shield((0, 3), 3, 5) # Large Shield
        build_shield((0, 4), 4, 6) # Spiked Shield
        build_shield((0, 5), 5, 7) # Magic Shield
        build_shield((0, 6), 6, 8) # Jewelled Shield

        def build_armour(description_index: tuple[int,int], short_index: int, dra_values_index: int):
            build_item(description_index, short_index, dra_values_index, Slot.BODY, TileId.ARMOUR, RuneId.ARMOR)

        # Armour
        build_armour((0,  7),    7,  9) # Cloth Armour
        build_armour((0,  8),    8, 10) # Leather Armour
        build_armour((2,  3), None, 11) # Ring Mail
        build_armour((0,  9),    9, 12) # Scale Main
        build_armour((0, 10),   10, 13) # Chain Mail
        build_armour((0, 11),   11, 14) # Plate Mail
        build_armour((0, 12),   12, 15) # Mystic Armour

        def build_weapon(description_index: tuple[int,int], short_index: int, dra_values_index: int, two_handed: bool = False, rune_id: RuneId = RuneId.SWORD):
            slot = Slot.TWO_HAND if two_handed else Slot.ONE_HAND
            build_item(description_index, short_index, dra_values_index, slot, TileId.WEAPON, rune_id)

        build_weapon((2,  4), None, 16) # Dagger	        2	4	None
        build_weapon((2,  6), None, 17) # Sling	            2 	6	None
        build_weapon((2,  7), None, 18) # Club	            2	7	None
        build_weapon((1,  0),   13, 19) # Flaming Oil	    1	0	  13
        build_weapon((1,  1),   14, 20) # Main Gauche	    1	1	  14
        build_weapon((2,  9), None, 21) # Spear	            2	9	None
        build_weapon((1,  2),   15, 22) # Throwing Axe	    1	2	  15
        build_weapon((1,  3),   16, 23) # Short Sword	    1	3	  16
        build_weapon((2, 10), None, 24) # Mace	            2	10	None
        build_weapon((1,  4),   17, 25) # Morning Star	    1	4	  17
        build_weapon((2, 12), None, 26) # Bow	            2	12	None

        build_weapon((2, 15), None, 28) # Crossbow	        2	15	None

        build_weapon((2, 19), None, 30) # Long Sword	    2	19	None
        build_weapon((2, 21), None, 31) # 2H Hammer	        2	21	None
        build_weapon((2, 22), None, 32) # 2H Axe	        2	22	None
        build_weapon((2, 24), None, 33) # 2H Sword	        2	24	None
        build_weapon((2, 26), None, 34) # Halberd	        2	26	None
        build_weapon((1,  5),   18, 35) # Chaos Sword	    1	5	  18
        build_weapon((2, 27), None, 36) # Magic Bow	        2	27	None
        build_weapon((1,  6),   19, 37) # Silver Sword	    1	6	  19
        build_weapon((2, 28), None, 38) # Magic Axe	        2	28	None
        build_weapon((1,  7),   20, 39) # Glass Sword	    1	7	  20
        build_weapon((1,  8),   21, 40) # Jewelled Sword	1	8	  21
        build_weapon((1,  9),   22, 41) # Mystic Sword	    1	9	  22

        #
        # TODO: RINGS AND AMULETS
        #

        def build_ring(description_index: tuple[int,int], short_index: int, dra_values_index: int):
            build_item(description_index, short_index, dra_values_index, Slot.FINGER, TileId.RING, RuneId.RING)

        build_ring((3,0),23,42) # Inv. Ring
        build_ring((3,1),24,43) # Prot. Ring
        build_ring((3,2),25,44) # Regen Ring

        def build_amulet(description_index: tuple[int,int], short_index: int, dra_values_index: int, rune_id: RuneId):
            build_item(description_index, short_index, dra_values_index, Slot.NECK, TileId.AMULET, rune_id)

        build_amulet((3, 3),None,45,RuneId.AMULET) # Amulet of Turning
        build_amulet((3, 4),None,46,RuneId.AMULET) # Spiked Collar
        build_amulet((2,29),None,None,RuneId.ANKH) # Ankh 

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

    '''
    rda_values = zip(dataOvl.range_values, dataOvl.defense_values, dataOvl.attack_values)
    min_range = min(len(dataOvl.range_values), len(dataOvl.defense_values), len(dataOvl.attack_values))
    max_range = max(len(dataOvl.range_values), len(dataOvl.defense_values), len(dataOvl.attack_values))
    for i in range(max_range):
        r = dataOvl.range_values[i]   if i < len(dataOvl.range_values)   else None
        d = dataOvl.defense_values[i] if i < len(dataOvl.defense_values) else None
        a = dataOvl.attack_values[i]  if i < len(dataOvl.attack_values)  else None
        print(",".join(map(lambda x: str(x),[r,d,a])))

    descriptions_weapons = to_strs(dataOvl.weapon_strings)
    descriptions_weapons_plus10 = to_strs(dataOvl.weapon_strings_plus10)

    for name in descriptions_weapons + descriptions_weapons_plus10:
        print(str(name)[2:].replace("'", ""))
    '''
