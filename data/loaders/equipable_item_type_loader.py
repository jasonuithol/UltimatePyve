from data.global_registry import GlobalRegistry

from models.data_ovl            import DataOVL
from models.enums.equipable_item_rune_id import EquipableItemRuneId
from models.enums.equipable_item_slot import EquipableItemSlot
from models.enums.equipable_item_tile_id import EquipableItemTileId
from models.enums.inventory_offset  import InventoryOffset
from models.equipable_items import EquipableItemType


class EquipableItemTypeLoader:

    # Injectable
    dataOvl: DataOVL
    global_registry: GlobalRegistry
        
    def build(self):

#        mysterious_indexes_armour = to_ints(dataOvl.armor_index_plus10)
    
        descriptions_armour = DataOVL.to_strs(self.dataOvl.armour_strings)
        descriptions_weapons = DataOVL.to_strs(self.dataOvl.weapon_strings)
        descriptions_weapons_plus10 = DataOVL.to_strs(self.dataOvl.weapon_strings_plus10)
        descriptions_rings_amulets = DataOVL.to_strs(self.dataOvl.ring_amulet_strings)
    
        descriptions = [
            descriptions_armour,
            descriptions_weapons,
            descriptions_weapons_plus10,
            descriptions_rings_amulets
        ]

        shortened_names = DataOVL.to_strs(self.dataOvl.shortened_names)

        defence_values  = DataOVL.to_ints(self.dataOvl.defense_values)
        range_values    = DataOVL.to_ints(self.dataOvl.range_values)
        attack_values   = DataOVL.to_ints(self.dataOvl.attack_values)        

        def build_item(description_index: tuple[int,int], short_index: int, dra_values_index: int, slot: EquipableItemSlot, tile_id: EquipableItemTileId, rune_id: EquipableItemRuneId):

            inventory_offset_value = dra_values_index + InventoryOffset.LEATHER_HELM.value
            inventory_offset = InventoryOffset(inventory_offset_value)

            item_type = EquipableItemType(
                # ItemType
                item_id = dra_values_index,
                inventory_offset = inventory_offset,
                tile_id = tile_id.value,
                name = descriptions[description_index[0]][description_index[1]],

                # EquipableItemType
                short_name = None if short_index is None else shortened_names[short_index],
                range_ = 0 if dra_values_index >= len(range_values) else range_values[dra_values_index],
                defence = 0 if dra_values_index >= len(defence_values) else defence_values[dra_values_index],
                attack = 0 if dra_values_index >= len(attack_values) else attack_values[dra_values_index],
                slot = slot,
                rune_id = rune_id
            )
            self.global_registry.item_types.register(dra_values_index, item_type)
            print(f"[items] Registered equippable item type: name={item_type.name}")
        
        def build_helm(description_index: tuple[int,int], short_index: int, dra_values_index: int):
            build_item(description_index, short_index, dra_values_index, EquipableItemSlot.HEAD, EquipableItemTileId.HELM, EquipableItemRuneId.HELM)

        # Helms
        build_helm((0, 0),    0, 0) # Leather Helm
        build_helm((2, 0), None, 1) # Chain Coif
        build_helm((2, 2), None, 2) # Iron Helm
        build_helm((0, 1),    1, 3) # Spiked Helm
        
        def build_shield(description_index: tuple[int,int], short_index: int, dra_values_index: int):
            build_item(description_index, short_index, dra_values_index, EquipableItemSlot.ONE_HAND, EquipableItemTileId.SHIELD, EquipableItemRuneId.SHIELD)

        # Shields
        build_shield((0, 2), 2, 4) # Small Shield
        build_shield((0, 3), 3, 5) # Large Shield
        build_shield((0, 4), 4, 6) # Spiked Shield
        build_shield((0, 5), 5, 7) # Magic Shield
        build_shield((0, 6), 6, 8) # Jewelled Shield

        def build_armour(description_index: tuple[int,int], short_index: int, dra_values_index: int):
            build_item(description_index, short_index, dra_values_index, EquipableItemSlot.BODY, EquipableItemTileId.ARMOUR, EquipableItemRuneId.ARMOR)

        # Armour
        build_armour((0,  7),    7,  9) # Cloth Armour
        build_armour((0,  8),    8, 10) # Leather Armour
        build_armour((2,  3), None, 11) # Ring Mail
        build_armour((0,  9),    9, 12) # Scale Main
        build_armour((0, 10),   10, 13) # Chain Mail
        build_armour((0, 11),   11, 14) # Plate Mail
        build_armour((0, 12),   12, 15) # Mystic Armour

        def build_weapon(description_index: tuple[int,int], short_index: int, dra_values_index: int, two_handed: bool = False, rune_id: EquipableItemRuneId = EquipableItemRuneId.SWORD):
            slot = EquipableItemSlot.TWO_HAND if two_handed else EquipableItemSlot.ONE_HAND
            build_item(description_index, short_index, dra_values_index, slot, EquipableItemTileId.WEAPON, rune_id)

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
            build_item(description_index, short_index, dra_values_index, EquipableItemSlot.FINGER, EquipableItemTileId.RING, EquipableItemRuneId.RING)

        build_ring((3,0),23,42) # Inv. Ring
        build_ring((3,1),24,43) # Prot. Ring
        build_ring((3,2),25,44) # Regen Ring

        def build_amulet(description_index: tuple[int,int], short_index: int, dra_values_index: int, rune_id: EquipableItemRuneId):
            build_item(description_index, short_index, dra_values_index, EquipableItemSlot.NECK, EquipableItemTileId.AMULET, rune_id)

        build_amulet((3, 3),None,45,EquipableItemRuneId.AMULET) # Amulet of Turning
        build_amulet((3, 4),None,46,EquipableItemRuneId.AMULET) # Spiked Collar
        build_amulet((2,29),None,47,EquipableItemRuneId.ANKH) # Ankh 

#
# MAIN
#
if __name__ == "__main__":

    registry = GlobalRegistry()
    registry._after_inject()

    loader = EquipableItemTypeLoader()
    loader.dataOvl = DataOVL.load()
    loader.global_registry = registry

    loader.build()
    for item in registry.item_types.values():
        print(f"ItemType: item_id={item.item_id}, tile_name={item.tile_id}, tile_id={item.tile_id.value}, name={item.name}")