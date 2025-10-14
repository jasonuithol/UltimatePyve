class CharacterRecord:
    LENGTH = 32

    def __init__(self, raw: bytearray, offset: int):
        self._raw = raw
        self._offset = offset

    def _get_u8(self, rel):
        return self._raw[self._offset + rel]

    def _set_u8(self, rel, val):
        if not (0 <= val <= 255):
            raise ValueError("Byte out of range")
        self._raw[self._offset + rel] = val

    def _get_u16(self, rel):
        return int.from_bytes(self._raw[self._offset + rel:self._offset + rel + 2], 'little')

    def _set_u16(self, rel, val):
        self._raw[self._offset + rel:self._offset + rel + 2] = val.to_bytes(2, 'little')

    @property
    def name(self) -> str:
        raw_name = self._raw[self._offset:self._offset + 9]
        return raw_name.split(b'\x00', 1)[0].decode('ascii', errors='ignore')

    @name.setter
    def name(self, value: str):
        b = value.encode('ascii')[:8]  # max 8 chars
        b = b + b'\x00' * (9 - len(b))
        self._raw[self._offset:self._offset + 9] = b

    @property
    def gender(self) -> int:
        return self._get_u8(9)

    @gender.setter
    def gender(self, val: int):
        self._set_u8(9, val)

    @property
    def char_class(self) -> str:
        return chr(self._get_u8(0xA))

    @char_class.setter
    def char_class(self, val: str):
        self._set_u8(0xA, ord(val[0]))

    @property
    def status(self) -> str:
        return chr(self._get_u8(0xB))

    @status.setter
    def status(self, val: str):
        self._set_u8(0xB, ord(val[0]))

    @property
    def strength(self) -> int:
        return self._get_u8(0xC)

    @strength.setter
    def strength(self, val: int):
        self._set_u8(0xC, val)

    @property
    def dexterity(self) -> int:
        return self._get_u8(0xD)

    @dexterity.setter
    def dexterity(self, val: int):
        self._set_u8(0xD, val)

    @property
    def intelligence(self) -> int:
        return self._get_u8(0xE)

    @intelligence.setter
    def intelligence(self, val: int):
        self._set_u8(0xE, val)

    @property
    def current_mp(self) -> int:
        return self._get_u8(0xF)

    @current_mp.setter
    def current_mp(self, val: int):
        self._set_u8(0xF, val)

    @property
    def current_hp(self) -> int:
        return self._get_u16(0x10)

    @current_hp.setter
    def current_hp(self, val: int):
        self._set_u16(0x10, val)

    @property
    def max_hp(self) -> int:
        return self._get_u16(0x12)

    @max_hp.setter
    def max_hp(self, val: int):
        self._set_u16(0x12, val)

    @property
    def experience(self) -> int:
        return self._get_u16(0x14)

    @experience.setter
    def experience(self, val: int):
        self._set_u16(0x14, val)

    @property
    def level(self) -> int:
        return self._get_u8(0x16)

    @level.setter
    def level(self, val: int):
        self._set_u8(0x16, val)

    @property
    def months_at_inn(self) -> int:
        return self._get_u8(0x17)

    @months_at_inn.setter
    def months_at_inn(self, val: int):
        self._set_u8(0x17, val)

    @property
    def unknown_0x18(self) -> int:
        return self._get_u8(0x18)

    @unknown_0x18.setter
    def unknown_0x18(self, val: int):
        self._set_u8(0x18, val)

    @property
    def helmet(self) -> int:
        return self._get_u8(0x19)

    @helmet.setter
    def helmet(self, val: int):
        self._set_u8(0x19, val)

    @property
    def armor(self) -> int:
        return self._get_u8(0x1A)

    @armor.setter
    def armor(self, val: int):
        self._set_u8(0x1A, val)

    @property
    def left_hand(self) -> int:
        return self._get_u8(0x1B)

    @left_hand.setter
    def left_hand(self, val: int):
        self._set_u8(0x1B, val)

    @property
    def right_hand(self) -> int:
        return self._get_u8(0x1C)

    @right_hand.setter
    def right_hand(self, val: int):
        self._set_u8(0x1C, val)

    @property
    def ring(self) -> int:
        return self._get_u8(0x1D)

    @ring.setter
    def ring(self, val: int):
        self._set_u8(0x1D, val)

    @property
    def amulet(self) -> int:
        return self._get_u8(0x1E)

    @amulet.setter
    def amulet(self, val: int):
        self._set_u8(0x1E, val)

    @property
    def inn_party_flag(self) -> int:
        return self._get_u8(0x1F)

    @inn_party_flag.setter
    def inn_party_flag(self, val: int):
        self._set_u8(0x1F, val)


