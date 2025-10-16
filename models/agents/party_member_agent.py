import math
import random

from enum import Enum

from dark_libraries.dark_math import Coord
from data.global_registry     import GlobalRegistry

from models.enums.character_class_to_tile_id import CharacterClassToTileId
from models.enums.npc_tile_id import NpcTileId

from models.character_record  import CharacterRecord
from models.equipable_items   import EquipableItemType
from models.sprite            import Sprite
from models.enums.equipable_item_slot import EquipableItemSlot

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
    rune_id          = None
)

class IncreasableSkillNames(Enum):
    STR = 'strength'
    DEX = 'dexterity'
    INT = 'intelligence'    

class PartyMemberAgent(CombatAgent):

    # TODO: This will be None for the moment
    global_registry: GlobalRegistry

    def __init__(self, sprite: Sprite, character_record: CharacterRecord):
        super().__init__(coord = None, sprite = sprite)
        self._character_record = character_record
        self._tile_id = CharacterClassToTileId.__dict__[character_record.char_class].value
        self._mana = self._calculate_maximum_mana()
        self._level = self._calculate_potential_level()

    def enter_combat(self, coord: Coord):
        self.coord = coord
        self._spent_action_points = 0

    def exit_combat(self):
        self.coord = None

    def is_in_combat(self):
        return not self.coord is None

    def get_weapons(self):
        lh_item = self.global_registry.item_types.get(self._character_record.left_hand)
        rh_item = self.global_registry.item_types.get(self._character_record.right_hand)
        helmet  = self.global_registry.item_types.get(self._character_record.helmet)

        equipped = [lh_item, rh_item, helmet]
        weapons  = [item for item in equipped if not item is None and item.attack > 0]
        if not any(weapons): 
            weapons = [BARE_HANDS]
        return weapons

    def armed_with_description(self) -> str:
        return "armed with " + ", ".join([weapon.name for weapon in self.get_weapons()])

    # NPC_AGENT IMPLEMENTATION (Completion): Start
    #
    @property
    def tile_id(self) -> int:
        return self._tile_id

    @property
    def name(self) -> str:
        return self._character_record.name
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

    def get_damage(self, attack_type: chr) -> int:
        if attack_type in ['R','B']:
            item_id = self._character_record.right_hand
        else: 
            item_id = self._character_record.left_hand
        equipable_item_type: EquipableItemType = self.global_registry.item_types.get(item_id)
        if equipable_item_type is None:
            self.log(f"WARNING: Could not obtain equipable_item_type for item_id={item_id}")
            return 1
        else:
            damage = equipable_item_type.attack
            if damage == 0:
                self.log(f"ERROR: equipable_item_type={equipable_item_type.name} for item_id={item_id} has zero damage.")
            return damage

    #
    # COMBAT_AGENT IMPLEMENTATION: End

    def _calculate_potential_level(self) -> int:
        return math.log(self._character_record.experience // 100, 2)

    def _calculate_maximum_mana(self) -> int:
        class_multipliers = {
            NpcTileId.ADVENTURER.value : 1.0,
            NpcTileId.MAGE.value       : 1.0,
            NpcTileId.BARD.value       : 0.5
        }
        return class_multipliers.get(self.tile_id, 0.0) * self._character_record.intelligence
        
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
        while self._level != self._calculate_potential_level():
            if self._level < self._calculate_potential_level():
                self._level += 1
                increased_skill_name = self._choose_increasable_skill()
                if increased_skill_name:
                    self._increase_skill(increased_skill_name, amount = 1)
            else:
                # Getting killed will result in loss of experience, so a level drop is possible.
                # This does not affect skill levels tho.
                # This allows absolute sweatlords to level every skill to 30 for all party members.
                self._level -= 1



    