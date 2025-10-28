import math
import random

from enum import Enum

from dark_libraries.dark_math import Coord
from data.global_registry     import GlobalRegistry

from models.enums.character_class_to_tile_id import CharacterClassToTileId
from models.enums.npc_tile_id import NpcTileId

from models.character_record  import CharacterRecord
from models.equipable_item_type   import EquipableItemType
from models.sprite            import Sprite
from models.enums.equipable_item_slot import EquipableItemSlot
from models.tile import Tile

from .combat_agent import CombatAgent

MAXIMUM_SKILL_LEVEL = 30

BARE_HANDS = EquipableItemType(
    item_id          = -1,
    inventory_offset = None,
    tile_id          = -1,
    name             = "Bare Hands",
    short_name       = "Bare Hands",
    range_           = 1,
    defence          = 0,
    attack           = 1,
    slot             = EquipableItemSlot.TWO_HAND,
    rune_id          = None,
    weight           = 0
)

EQUIPMENT_PROPERTY_NAMES = [
    'helmet',
    'amulet',
    'armor',
    'left_hand',
    'right_hand',
    'ring'
]

EQUIPMENT_SLOT_TO_PROPNAME_MAP = {
    EquipableItemSlot.HEAD     : ['helmet'],
    EquipableItemSlot.BODY     : ['armor' ],
    EquipableItemSlot.NECK     : ['amulet'],
    EquipableItemSlot.FINGER   : ['ring'  ],

    EquipableItemSlot.TWO_HAND : ['left_hand', 'right_hand'],
    EquipableItemSlot.ONE_HAND : ['left_hand', 'right_hand']
}

class IncreasableSkillNames(Enum):
    STR = 'strength'
    DEX = 'dexterity'
    INT = 'intelligence'    

class PartyMemberAgent(CombatAgent):

    # TODO: This will be None for the moment
    global_registry: GlobalRegistry

    def __init__(self, sprite: Sprite[Tile], character_record: CharacterRecord):
        super().__init__(coord = None, sprite = sprite)
        self._character_record = character_record
        self._tile_id = CharacterClassToTileId.__dict__[character_record.char_class].value.value

    def enter_combat(self, coord: Coord[int]):
        self.coord = coord
        self._spent_action_points = 0

    def exit_combat(self):
        self.coord = None

    def get_equipped_item_codes(self) -> list[int]:
        return [
            int(getattr(self._character_record, name))
            for name in EQUIPMENT_PROPERTY_NAMES
        ]

    def get_equipped_items(self) -> list[EquipableItemType]:
        item_codes = self.get_equipped_item_codes()

        return [
            self.global_registry.item_types.get(item_code)
            for item_code in item_codes
            if item_code != 255
        ]

    def has_equipped_item(self, item_id: int) -> bool:
        item_codes = self.get_equipped_item_codes()
        return item_id in item_codes

    def is_slot_available(self, slot: EquipableItemSlot) -> bool:
        prop_names = EQUIPMENT_SLOT_TO_PROPNAME_MAP[slot]
        available_props = [prop_name for prop_name in prop_names if getattr(self._character_record, prop_name) == 255]
        if slot == EquipableItemSlot.TWO_HAND:
            return len(available_props) >= 2
        else:
            return len(available_props) >= 1

    def can_carry_extra_weight(self, item: EquipableItemType):
        current_carried_weight = sum(item.weight for item in self.get_equipped_items())
        return current_carried_weight + item.weight <= self.strength

    def unequip_item(self, item_id: int):
        assert self.has_equipped_item(item_id), f"Item ({item_id}) not equipped: {self.get_equipped_item_codes()}"

        for prop_name in EQUIPMENT_PROPERTY_NAMES:
            if int(getattr(self._character_record, prop_name)) == item_id:
                self.log(f"Unequipping {prop_name}(item_id={item_id}) from {self.name}")
                setattr(self._character_record, prop_name, 255)

    def equip_item(self, item_id: int):
        assert not self.has_equipped_item(item_id), f"Item ({item_id}) already equipped: {self.get_equipped_item_codes()}"

        item: EquipableItemType = self.global_registry.item_types.get(item_id)
        assert self.is_slot_available(item.slot), f"Item slot ({item.slot}) not available"

        prop_names = EQUIPMENT_SLOT_TO_PROPNAME_MAP[item.slot]
        for prop_name in prop_names:
            if getattr(self._character_record, prop_name) == 255:
                setattr(self._character_record, prop_name, item_id)
                if item.slot == EquipableItemSlot.ONE_HAND:
                    self.log(f"Equipped {self.name}'s {item.slot.name} with (item_id={item_id})")
                    break

    def get_weapons(self) -> list[EquipableItemType]:
        equipped = self.get_equipped_items()
        weapons  = [item for item in equipped if not item is None and item.attack > 0]
        if not any(weapons): 
            weapons = [BARE_HANDS]
        return weapons

    def armed_with_description(self) -> str:
        return ", ".join([weapon.name for weapon in self.get_weapons()])

    # NPC_AGENT IMPLEMENTATION (Completion): Start
    #
    @property
    def tile_id(self) -> int:
        return self._tile_id

    @property
    def name(self) -> str:
        n = self._character_record.name
        if len(n.strip()) == 0:
            return "oroborus"
        else:
            return n
    #
    # NPC_AGENT IMPLEMENTATION (Completion): End

    # COMBAT_AGENT IMPLEMENTATION: Start
    #
    @property
    def strength(self) -> int:
        return self._character_record.strength

    @property
    def dexterity(self) -> int:
        return self._character_record.dexterity

    @property
    def armour(self) -> int:
        item_id = self._character_record.armor
        equipable_item_type: EquipableItemType = self.global_registry.item_types.get(item_id)
        return equipable_item_type.attack

    @property
    def maximum_hitpoints(self) -> int:
        return self._character_record.max_hp

    @property 
    def hitpoints(self) -> int:
        return self._character_record.current_hp

    @hitpoints.setter
    def hitpoints(self, val: int):
        self._character_record.current_hp = val

    def get_damage(self, weapon: EquipableItemType) -> int:
        damage = weapon.attack
        if damage == 0:
            self.log(f"WARNING: weapon '{weapon.name}' (item_id={weapon.item_id}) has zero damage.")
        return damage

    #
    # COMBAT_AGENT IMPLEMENTATION: End

    @property
    def level(self) -> int:
        return int(self._character_record.level)

    @level.setter
    def level(self, val: int):
        self._character_record.level = val

    def _calculate_potential_level(self) -> int:
        return int(math.log(self._character_record.experience // 100, 2))

    @property
    def maximum_mana(self) -> int:
        return self._calculate_maximum_mana()

    @property 
    def mana(self) -> int:
        return self._character_record.current_mp

    @mana.setter
    def mana(self, val: int):
        self._character_record.current_mp = val
        
    def _calculate_maximum_mana(self) -> int:
        class_multipliers = {
            NpcTileId.ADVENTURER.value : 1.0,
            NpcTileId.MAGE.value       : 1.0,
            NpcTileId.BARD.value       : 0.5
        }
        return int(class_multipliers.get(self.tile_id, 0.0) * self._character_record.intelligence)

    @property
    def intelligence(self) -> int:
        return self._character_record.intelligence

    def _increase_skill(self, increased_skill_name: str, amount: int):
        current_skill_value = getattr(self._character_record, increased_skill_name)
        setattr(self._character_record, increased_skill_name, max(current_skill_value + amount, MAXIMUM_SKILL_LEVEL))

    def _choose_increasable_skill(self) -> str | None:
        eligible_skills = [
            skill_name 
            for skill_name in IncreasableSkillNames
            if getattr(self._character_record, skill_name.value) < MAXIMUM_SKILL_LEVEL
        ]

        random.shuffle(eligible_skills)
        return next(eligible_skills, None)

    #
    # Public Methods
    #     

    def add_experience(self, delta: int):
        self._character_record.experience = min(self._character_record.experience + delta, 0)

    def update_level(self):
        while self.level != self._calculate_potential_level():
            if self.level < self._calculate_potential_level():
                self.level += 1
                increased_skill_name = self._choose_increasable_skill()
                if increased_skill_name:
                    self._increase_skill(increased_skill_name, amount = 1)
            else:
                # Getting killed will result in loss of experience, so a level drop is possible.
                # This does not affect skill levels tho.
                # This allows absolute sweatlords to level every skill to 30 for all party members.
                self.level -= 1



    