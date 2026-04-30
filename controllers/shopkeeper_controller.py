import struct

import pygame

from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.party_agent    import PartyAgent
from models.agents.town_npc_agent import TownNpcAgent
from models.enums.inventory_offset import InventoryOffset
from models.party_inventory       import PartyInventory

from services.console_service    import ConsoleService
from services.info_panel_service import InfoPanelService
from services.input_service      import InputService, keycode_to_char


# Lower 7 bits of dialog_number identify the shopkeeper's role. These match the
# town-membership tables in DATA.OVL (shoppe_*_indexes), confirmed empirically
# against TOWNE.NPC.
ROLE_ARMS_SELLER  = 1
ROLE_TAVERN       = 2
ROLE_STABLEMAN    = 3
ROLE_SHIPWRIGHT   = 4
ROLE_REAGENT      = 5
ROLE_PROVISIONER  = 6
ROLE_HEALER       = 7
ROLE_INNKEEPER    = 8


# DATA.OVL stock/price tables index items 0x00..0x2E. Those map linearly to the
# InventoryOffset range 0x21A..0x248 (armour → weapons → rings/amulets).
_STOCK_BASE_OFFSET = 0x21A
_STOCK_TERMINATOR  = 0xFF
_STOCK_ROW_BYTES   = 8

# Britain's arms-seller stocks row 0 of merchant_weapon_lists (Iolo's-Bows-style
# inventory: dagger, sling, bows, crossbow, arrows, quarrels, magic bow).
# The other eight rows correspond to the remaining armoury locations; exact
# mapping is TBD, so this is hardcoded for the Britain-only slice.
_BRITAIN_ARMS_ROW = 0


class ShopkeeperController(LoggerMixin):

    # Injectable
    party_agent:        PartyAgent
    party_inventory:    PartyInventory
    global_registry:    GlobalRegistry
    console_service:    ConsoleService
    info_panel_service: InfoPanelService
    input_service:      InputService

    def __init__(self):
        super().__init__()
        self._cached_prices: list[int] | None = None

    # ------------------------------------------------------------------
    # Entry point — dispatched from ConversationController when an NPC's
    # dialog_number has the high bit set (0x80). The lower 7 bits give the
    # shopkeeper's role.
    # ------------------------------------------------------------------
    def talk(self, npc: TownNpcAgent):
        role = npc.dialog_number & 0x7F
        if role == ROLE_ARMS_SELLER:
            self._arms_seller(npc)
        else:
            self.log(
                f"Shopkeeper role {role} (dialog_number=0x{npc.dialog_number:02x}) "
                "not yet implemented"
            )
            self._npc_speak("I have no time to talk just now.")

    # ------------------------------------------------------------------
    # Arms seller — Britain (Terrance) for now. Greeting line is hardcoded
    # in DATA.OVL at 0x7f58. The input loop must never fall back to a
    # generic open prompt — outer keys are always B/S, item lists are
    # always indexed a..z.
    # ------------------------------------------------------------------
    def _arms_seller(self, npc: TownNpcAgent):
        self._npc_speak("Welcome to mine shoppe!")
        self._npc_speak(f"I am {npc.name}, weapons-master.")
        while True:
            answer = self._read_keypress(prompt="B)uy or S)ell?")
            if answer is None:  # ESC exits the conversation
                self._npc_speak("Fare thee well!")
                return
            if answer == "b":
                self._buy(_BRITAIN_ARMS_ROW)
            elif answer == "s":
                self._sell()

    # ------------------------------------------------------------------
    # Buy / sell mechanics
    # ------------------------------------------------------------------
    def _buy(self, row_index: int):
        stock = self._stock_for_row(row_index)
        if not stock:
            self._npc_speak("My shelves are bare today.")
            return

        while True:
            self._npc_speak("I have for sale:")
            for i, (label, _offset, _price) in enumerate(stock):
                self.console_service.print_ascii(
                    f"{chr(ord('a') + i)}...{label}", no_prompt=True
                )

            pick = self._read_keypress(prompt="Which?")
            if pick is None:  # ESC returns to outer Buy/Sell prompt
                return

            idx = ord(pick) - ord('a')
            if not 0 <= idx < len(stock):
                self._npc_speak("I have no such thing!")
                continue
            label, offset, price = stock[idx]

            self._npc_speak(self._describe(label, offset, price))
            if self._read_keypress(prompt="Buy? Y)es N)o") != "y":
                self._npc_speak("Mayhap another time.")
                continue

            if not self.party_inventory.has(InventoryOffset.GOLD, price):
                self._npc_speak("Thou hast not the gold!")
                continue

            if self.party_inventory.read(offset) >= self.party_inventory.max(offset):
                self._npc_speak("Thou canst carry no more!")
                continue

            self.party_inventory.use(InventoryOffset.GOLD, price)
            self.party_inventory.safe_add(offset, 1)
            self.info_panel_service.update_party_summary()
            self._npc_speak(f"Here is thy {label}!")

    def _sell(self):
        while True:
            sellable = self._sellable_inventory()
            if not sellable:
                self._npc_speak("Thou hast nothing of worth!")
                return

            self._npc_speak("I will buy:")
            for i, (label, _offset, offer, count) in enumerate(sellable):
                self.console_service.print_ascii(
                    f"{chr(ord('a') + i)}...{label} x{count}: {offer} gp",
                    no_prompt=True,
                )

            pick = self._read_keypress(prompt="Which?")
            if pick is None:  # ESC returns to outer Buy/Sell prompt
                return

            idx = ord(pick) - ord('a')
            if not 0 <= idx < len(sellable):
                self._npc_speak("Thou hast no such thing!")
                continue
            label, offset, offer, _ = sellable[idx]

            if not self.party_inventory.use(offset, 1):
                self._npc_speak("Thou hast no such thing!")
                continue
            self.party_inventory.safe_add(InventoryOffset.GOLD, offer)
            self.info_panel_service.update_party_summary()
            self._npc_speak(f"Here is thy gold for the {label}!")

    def _sellable_inventory(self) -> list[tuple[str, InventoryOffset, int, int]]:
        # Items 0x00..0x2E cover armour, weapons, rings, amulets — the full set
        # any arms-seller will buy. Items priced 0 in base_prices_awr are quest
        # uniques (Mystic *, Chaos Sword, Glass Sword, Jeweled Sword) — skip.
        prices = self._base_prices()
        out: list[tuple[str, InventoryOffset, int, int]] = []
        for byte in range(0x2F):
            offset = self._row_byte_to_offset(byte)
            if offset is None:
                continue
            base = prices[byte]
            if base == 0:
                continue
            count = self.party_inventory.read(offset)
            if count <= 0:
                continue
            offer = max(1, base // 2)
            out.append((self._item_label(offset), offset, offer, count))
        return out

    # ------------------------------------------------------------------
    # Data-access helpers
    # ------------------------------------------------------------------
    def _stock_for_row(self, row_index: int) -> list[tuple[str, InventoryOffset, int]]:
        raw = self.global_registry.data_ovl.merchant_weapon_lists
        start = row_index * _STOCK_ROW_BYTES
        row = raw[start:start + _STOCK_ROW_BYTES]
        prices = self._base_prices()
        out: list[tuple[str, InventoryOffset, int]] = []
        for byte in row:
            if byte == _STOCK_TERMINATOR:
                break
            offset = self._row_byte_to_offset(byte)
            if offset is None:
                continue
            price = prices[byte]
            if price == 0:
                continue
            out.append((self._item_label(offset), offset, price))
        return out

    def _base_prices(self) -> list[int]:
        if self._cached_prices is None:
            raw = self.global_registry.data_ovl.base_prices_awr
            self._cached_prices = list(struct.unpack_from("<48H", raw, 0))
        return self._cached_prices

    @staticmethod
    def _row_byte_to_offset(byte: int) -> InventoryOffset | None:
        try:
            return InventoryOffset(_STOCK_BASE_OFFSET + byte)
        except ValueError:
            return None

    @staticmethod
    def _item_label(offset: InventoryOffset) -> str:
        return offset.name.replace("_", " ").title()

    def _describe(self, label: str, offset: InventoryOffset, price: int) -> str:
        # Combat stats live in three parallel byte tables in DATA.OVL, indexed
        # by the same item byte the stock and price tables use.
        byte = offset.value - _STOCK_BASE_OFFSET
        ovl = self.global_registry.data_ovl
        attack  = ovl.attack_values[byte]  if byte < len(ovl.attack_values)  else 0
        defense = ovl.defense_values[byte] if byte < len(ovl.defense_values) else 0
        rng     = ovl.range_values[byte]   if byte < len(ovl.range_values)   else 0
        parts: list[str] = []
        if attack:  parts.append(f"atk {attack}")
        if defense: parts.append(f"def {defense}")
        if rng:     parts.append(f"rng {rng}")
        if parts:
            return f"{label}: {', '.join(parts)}. {price} gp."
        return f"{label}: {price} gp."

    def _say(self, msg: str):
        self.console_service.print_ascii(msg, no_prompt=True)
        self.console_service.print_ascii("", no_prompt=True)

    def _npc_speak(self, msg: str):
        self._say(f'"{msg}"')

    def _read_keypress(self, prompt: str) -> str | None:
        # Single-keypress input: merchants act on the first letter immediately,
        # no Enter required. ESC returns None to drop back one menu level.
        self.console_service.print_ascii(prompt, no_prompt=True)
        self.console_service.print_ascii(":", include_carriage_return=False, no_prompt=True)
        while True:
            event = self.input_service.get_next_event()
            if getattr(event, "type", 0) == pygame.QUIT or getattr(event, "key", 0) == -1:
                return None
            if event.key == pygame.K_ESCAPE:
                self.console_service.print_ascii("", no_prompt=True)
                self.console_service.print_ascii("", no_prompt=True)
                return None
            char = keycode_to_char(event.key)
            if char is None or not char.isalpha():
                continue
            self.console_service.print_ascii(char, no_prompt=True)
            return char.lower()
