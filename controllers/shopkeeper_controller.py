import random
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


# SHOPPE.DAT string-index ranges used by the arms-seller path. Item descriptions
# start at index 8 and run in inventory-byte order, but quest items with a
# base price of 0 (Jewelled Shield, Mystic Armour, Chaos/Glass/Jeweled/Mystic
# Sword) have no description string — so the byte→index map is built at
# runtime by walking the price table. The sell-side variants vary the flavour
# text (battle-worn / inferior / excellent condition / ...); we pick one at
# random per transaction.
_ITEM_DESC_BASE = 8
_SELL_OFFER_RANGE = (49, 56)  # inclusive

# store_names is one big NUL-separated list. Britain's arms seller is the first
# entry ("Iolo's Bows"); the rest of the armouries follow in town order. The
# slice currently includes a few trailing mantra bytes from virtue_mantras, so
# we filter to entries we recognise rather than indexing positionally.
_BRITAIN_SHOPPE_NAME_NEEDLE = "Iolo"

# barkeeper_names is misnamed: it holds every shopkeeper's first name in role
# order (arms-sellers first, then taverns, etc). Britain's arms seller is the
# first entry — "Gwenneth". The TownNpcAgent only knows the spawner placeholder
# ("NPC#N"), so we look the canonical name up here.
_BRITAIN_ARMS_SELLER_NAME_INDEX = 0


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
        self._cached_desc_idx_by_byte: dict[int, int] | None = None

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
    # Arms seller — Britain (Terrance) for now. Welcome / greeting / farewell
    # text comes from DATA.OVL (~0x7836..0x8056). Item descriptions and sell
    # offers come from SHOPPE.DAT. Outer keys are always B/S; item lists are
    # always indexed a..z.
    # ------------------------------------------------------------------
    def _arms_seller(self, npc: TownNpcAgent):
        shoppe = self._shoppe_name()
        seller_name = self._arms_seller_name(_BRITAIN_ARMS_SELLER_NAME_INDEX)
        welcome = self._resolve(
            self._first_string(self.global_registry.data_ovl.shop_welcome_template),
            name=seller_name, shoppe=shoppe,
        )
        self._npc_speak(welcome)
        self._say(f"{seller_name} says,")
        greeting = self._random_string(
            self.global_registry.data_ovl.shop_buy_sell_greetings
        )
        # First iteration uses the canonical greeting as the keypress prompt so
        # the animated cursor sits one space after the "?". Subsequent passes
        # (after a buy/sell round) just wait for the next key with no prompt.
        prompt = f'"{greeting}"'
        while True:
            answer = self._read_keypress(prompt=prompt)
            prompt = ""
            if answer is None:  # ESC exits the conversation
                self._npc_speak(self._random_string(
                    self.global_registry.data_ovl.shop_farewells
                ))
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
            self._npc_speak(self._buy_list_intro())
            for i, (label, _offset, _price) in enumerate(stock):
                self.console_service.print_ascii(
                    f"{chr(ord('a') + i)}...{label}", no_prompt=True
                )

            pick = self._read_keypress(prompt=self._buy_pick_prompt())
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

            pick = self._read_keypress(prompt=self._sell_pick_prompt())
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
            self._npc_speak(self._sell_offer_line(label, offer))

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
        # Read the canonical sales pitch from SHOPPE.DAT. % is the price
        # placeholder. The byte→string-index map skips quest items with no
        # base price (no description string in SHOPPE.DAT for them).
        byte = offset.value - _STOCK_BASE_OFFSET
        idx = self._desc_idx_for_byte(byte)
        strings = self.global_registry.shoppe_strings
        if idx is not None and 0 <= idx < len(strings):
            return strings[idx].replace("%", str(price))
        return f"{label}: {price} gp."

    def _desc_idx_for_byte(self, byte: int) -> int | None:
        if self._cached_desc_idx_by_byte is None:
            mapping: dict[int, int] = {}
            next_idx = _ITEM_DESC_BASE
            for b, p in enumerate(self._base_prices()):
                if p > 0:
                    mapping[b] = next_idx
                    next_idx += 1
            self._cached_desc_idx_by_byte = mapping
        return self._cached_desc_idx_by_byte.get(byte)

    def _sell_offer_line(self, label: str, offer: int) -> str:
        # 49..56 are the eight sell-side flavour variants. & is the item name
        # placeholder, % is the gold offer.
        lo, hi = _SELL_OFFER_RANGE
        idx = random.randint(lo, hi)
        strings = self.global_registry.shoppe_strings
        if 0 <= idx < len(strings):
            return strings[idx].replace("&", label).replace("%", str(offer))
        return f"Here is thy gold for the {label}!"

    def _say(self, msg: str):
        self.console_service.print_ascii(msg, no_prompt=True)
        self.console_service.print_ascii("", no_prompt=True)

    def _npc_speak(self, msg: str):
        self._say(f'"{msg}"')

    # ------------------------------------------------------------------
    # DATA.OVL phrase helpers — strings live as NUL-separated ASCII
    # blocks at fixed offsets. Random variants are picked per call;
    # placeholders ($/#/@/&/%) are resolved against the current context.
    # ------------------------------------------------------------------
    def _split_strings(self, raw: bytes) -> list[str]:
        return [
            chunk.decode("ascii", errors="ignore").strip("\n").strip()
            for chunk in raw.split(b"\x00")
            if chunk.strip(b"\n")
        ]

    def _first_string(self, raw: bytes) -> str:
        items = self._split_strings(raw)
        return items[0] if items else ""

    def _random_string(self, raw: bytes) -> str:
        items = self._split_strings(raw)
        return random.choice(items) if items else ""

    def _time_of_day_word(self) -> str:
        words = self._split_strings(
            self.global_registry.data_ovl.time_of_day_strings
        )  # ["morning", "afternoon", "evening"]
        if len(words) < 3:
            return ""
        hour = self.global_registry.saved_game.read_current_datetime().hour
        if 5 <= hour < 12:
            return words[0]
        if 12 <= hour < 18:
            return words[1]
        return words[2]

    def _shoppe_name(self) -> str:
        # Britain arms seller is the only role wired today; look up "Iolo's
        # Bows" by content match so we don't depend on the (still-fuzzy)
        # store_names slice boundaries.
        raw = self.global_registry.data_ovl.store_names
        for chunk in raw.split(b"\x00"):
            text = chunk.decode("ascii", errors="ignore").strip()
            if _BRITAIN_SHOPPE_NAME_NEEDLE in text:
                return text
        return ""

    def _arms_seller_name(self, index: int) -> str:
        names = self._split_strings(self.global_registry.data_ovl.barkeeper_names)
        return names[index] if 0 <= index < len(names) else ""

    def _buy_pick_prompt(self) -> str:
        return f'"{self._random_string(self.global_registry.data_ovl.shop_buy_pick_prompts)}"'

    def _sell_pick_prompt(self) -> str:
        return f'"{self._random_string(self.global_registry.data_ovl.shop_sell_pick_prompts)}"'

    def _buy_list_intro(self) -> str:
        # Combines an optional affirmation with a list-preface — e.g.
        # "But of course! We've got:" or just "Thou canst buy:". The
        # affirmation appears about half the time, matching the original.
        preface = self._random_string(self.global_registry.data_ovl.shop_list_prefaces)
        if random.random() < 0.5:
            return preface
        affirmation = self._random_string(self.global_registry.data_ovl.shop_affirmations)
        return f"{affirmation} {preface}" if affirmation else preface

    def _resolve(self, template: str, *, name: str = "",
                 shoppe: str = "", item: str = "", price: int | None = None) -> str:
        out = template.strip().strip('"')
        out = out.replace("$", name)
        out = out.replace("#", shoppe)
        out = out.replace("@", self._time_of_day_word())
        out = out.replace("&", item)
        if price is not None:
            out = out.replace("%", str(price))
        return out

    def _read_keypress(self, prompt: str = "") -> str | None:
        # Single-keypress input: merchants act on the first letter immediately,
        # no Enter required. ESC returns None to drop back one menu level.
        # The animated cursor is drawn automatically at the current console
        # position by InteractiveConsole.draw(), so no explicit prompt glyph
        # is needed — printing the prompt inline (no carriage return) with a
        # trailing space puts the cursor one space after the last text.
        if prompt:
            self.console_service.print_ascii(
                f"{prompt} ", include_carriage_return=False, no_prompt=True
            )
        while True:
            event = self.input_service.get_next_event()
            if getattr(event, "type", 0) == pygame.QUIT or getattr(event, "key", 0) == -1:
                return None
            if event.key == pygame.K_ESCAPE:
                self.console_service.print_ascii("", no_prompt=True)
                return None
            char = keycode_to_char(event.key)
            if char is None or not char.isalpha():
                continue
            self.console_service.print_ascii(char, no_prompt=True)
            return char.lower()
