from typing import Iterable
from dark_libraries.logging import LoggerMixin
from data.global_registry   import GlobalRegistry
from models.enums.npc_ids   import NpcTileId
from models.npc_metadata    import NpcMetadata

HUMAN_DATA = """
Name|Str|Dex|Int|Armor|Damage|HP|Max n.|Treasure %|Special Attacks|Exp|Additional Notes
Child|8|8|8|0|0|5|1|0.00%|--|2|--
Beggar|8|8|8|0|0|5|1|0.00%|--|2|--
Villager|12|12|12|0|6|8|1|10.00%|--|3|--
Minstrel with lute|12|16|14|0|6|8|1|10.00%|--|3|--
Jester|12|18|12|0|6|8|1|10.00%|--|3|--
Merchant|12|12|18|0|6|8|1|10.00%|--|3|--
Guard|22|30|10|6|30|99|8|5.00%|--|25|Can throw axes
Mage|10|15|20|0|15|10|3|20.00%|--|3|Magic user
Bard|15|20|10|4|12|15|9|10.00%|--|4|Can shoot a bow
Fighter|20|15|10|8|15|20|6|15.00%|--|6|--
Adventurer|30|30|30|30|99|99|1|0.00%|--|-|Magic user, can teleport, body vanishes at death, never takes damage
Man in stocks|--|--|--|--|--|--|--|--|--|--|--
Man in manacles|--|--|--|--|--|--|--|--|--|--|--
"""

MONSTER_DATA = """
Name|Str|Dex|Int|Armor|Damage|HP|Max n.|Treasure %|Special Attacks|Exp|Additional Notes
Slime|6|6|2|0|4|10|16|0.00%|--|3|Can split in two, leaves no corpse, ambushes campers, common in dungeons
Rotworm|5|17|6|0|6|5|10|0.00%|Poison, plague|2|--
Giant spider|10|10|5|0|8|10|4|5.00%|Poison-spit|3|Ambushes campers, common in dungeons
Insect swarm|1|30|1|0|4|5|10|0.00%|--|2|Leaves no corpse
Giant rat|5|20|5|0|6|10|10|5.00%|Poison, plague|3|Ambushes campers, common in dungeons
Snake|5|18|8|1|8|10|4|0.00%|Poison-spit|3|--
Bat|5|30|5|0|6|5|16|0.00%|--|2|Leaves no corpse, ambushes campers, common in dungeons
Ghost|1|20|10|0|12|20|6|0.00%|--|6|Can become invisible, is undead, leaves no corpse, common in dungeons
Gremlin|10|21|10|2|4|10|13|12.00%|Steal|3|Ambushes campers, common in dungeons
Skeleton|10|20|5|0|12|20|8|13.00%|--|6|Undead
Orc|15|13|10|2|12|10|10|11.00%|--|3|Has bludgeoning attack
Shark|20|17|5|0|8|22|10|0.00%|--|6|Leave no corpse
Gazer|8|10|25|0|10|20|4|0.00%|Magic, charm|6|Common in dungeons
Headless|19|12|8|2|12|20|8|12.00%|--|6|Has bludgeoning attack, ambushes campers
Corpser|17|10|8|0|15|40|4|0.00%|--|11|--
Troll|18|17|9|4|15|15|4|15.00%|Shoot|4|Ambushes campers
Ettin|20|15|12|3|15|30|6|17.00%|Shoot|8|Has bludgeoning attack
Sea horse|17|20|20|2|10|30|3|0.00%|Magic|8|Leaves no corpse
Squid|24|20|8|0|20|50|2|0.00%|Shoot, poison-spit|13|Leaves no corpse
Mongbat|10|30|15|4|20|20|16|5.00%|--|6|--
Wisp|8|30|20|0|20|40|4|0.00%|Magic, charm|11|Can teleport, leaves no corpse
Mimic|20|30|12|3|15|30|1|20.00%|Poison|8|Has bludgeoning attack
Reaper|20|25|12|4|20|40|3|25.00%|Magic|11|Has bludgeoning attack, common in dungeons
Gargoyle|20|10|5|15|20|40|1|0.00%|--|11|Has bludgeoning attack, can split in two
Sea serpent|17|17|8|2|30|70|1|0.00%|Shoot|18|Leaves no corpse
Daemon|25|25|25|5|20|75|4|0.00%|Magic, summon, charm|13|Is undead, leaves no corpse
Sand trap|25|25|5|10|30|80|1|25.00%|--|21|--
Dragon|30|25|25|10|30|99|2|20.00%|Shoot, magic, summon|25|--
"""

QUEST_DATA = """
Name|Str|Dex|Int|Armor|Damage|HP|Max n.|Treasure %|Special Attacks|Exp|Additional Notes
Blackthorn|30|30|30|30|30|99|1|0.00%|--|--|Can summon a daemon, never takes damage, magic user, can teleport, body vanishes at death, can become invisible, can charm.
Shadowlord|25|30|30|10|30|99|1|0.00%|--|25|Magic user, can teleport, body vanishes at death, can become invisible, can charm, can poison, can infect with plague, is undead
"""

LORD_BRITISH_DATA = """
Name|Str|Dex|Int|Armor|Damage|HP|Max n.|Treasure %|Special Attacks|Exp|Additional Notes
Lord British|30|30|30|30|99|99|1|0.00%|--|--|--
Apparition|--|--|--|--|--|--|--|--|--|--|--
Mirror reflection|--|--|--|--|--|--|--|--|--|--|--
"""

def _to_npc_tile_id(name: str) -> int:
    member_name = name.upper().replace(" ", "_")
    tile_id: NpcTileId = NpcTileId.__dict__.get(member_name, None)
    assert not tile_id is None, f"Could not lookup NpcTileId for name '{name}'"
    return tile_id.value


class NpcMetadataLoader(LoggerMixin):

    global_registry: GlobalRegistry

    def _populate_special_abilities(self, meta: NpcMetadata, special_abilities_raw: set[str]):

        aliases = {
            "body_vanishes_at_death" : "leaves_no_corpse",
            "leave_no_corpse"        : "leaves_no_corpse",
            "summon"                 : "can_summon_a_daemon",
            "plague"                 : "poison_melee",
            "can_poison"             : "poison_melee",
            "poison"                 : "poison_melee",
            "can_infect_with_plague" : "poison_melee",
            "charm"                  : "can_charm",
            "steal"                  : "steals_food",
            "undead"                 : "is_undead",
            "magic"                  : "magic_missile",
            "magic_user"             : "magic_missile",
        }

        for ability in special_abilities_raw:
            ability_property_name = ability.lower().strip().replace(" ", "_").replace("-","_").replace(".","")

            if ability_property_name in ["", "__","can_throw_axes","can_shoot_a_bow","shoot"]:
                continue

            found_matching_property = False
            for extended_property_group in [
                meta.abilities_attack,
                meta.abilities_defence,
                meta.abilities_magic,
                meta.abilities_terrain
            ]:
                for original, alias in aliases.items():
                    if ability_property_name == original:
                        ability_property_name = alias

                if hasattr(extended_property_group, ability_property_name):
                    found_matching_property = True
                    setattr(extended_property_group, ability_property_name, True)
            if found_matching_property == False:
                self.log(f"WARNING: Could not find matching property for ability string '{ability}' -> '{ability_property_name}'")

    def _build_meta(self, data: list[str]) -> NpcMetadata:

        meta = NpcMetadata(
            name = data[0],
            npc_tile_id = _to_npc_tile_id(data[0]),
            general_stats = tuple(data[1:4]),  # Str|Dex|Int
            combat_stats  = tuple(data[4:7]),  # Armor|Damage|HP
            other_stats   = (                  # Max n.|Treasure %||Exp
                                data[ 7],
                                data[ 8],
                                data[10]
                            )
        )

        special_abilities_raw = set((data[9] + "," + data[11]).split(","))
        self._populate_special_abilities(meta, special_abilities_raw)
        return meta

    def _build(self, raw_data: str) -> Iterable[NpcMetadata]:
        for line in raw_data.splitlines():
            if len(line) == 0 or "Name|Str|Dex|Int|" in line:
                continue
            yield self._build_meta(line.split("|"))

    def load(self):
        for meta in self._build(HUMAN_DATA + MONSTER_DATA + QUEST_DATA + LORD_BRITISH_DATA):
            self.global_registry.npc_metadata.register(meta.npc_tile_id, meta)
        self.log(f"Registered {len(self.global_registry.npc_metadata)} metadata records for NPCs")

