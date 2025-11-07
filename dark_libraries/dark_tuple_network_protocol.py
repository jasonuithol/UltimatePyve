from typing import NamedTuple
from dark_libraries.dark_network import DarkNetworkProtocol

class DarkUtf8StringProtocol(DarkNetworkProtocol[str]):

    def __init__(self):
        self._buffer = b""

    def encode(self, message: str) -> bytes:
        return message.encode("utf-8") + b"\n"

    def decode(self, data: bytes) -> list[str]:
        self._buffer += data
        messages = []
        while b"\n" in self._buffer:
            line, self._buffer = self._buffer.split(b"\n", 1)
            messages.append(line.decode("utf-8", errors="replace"))
        return messages

class DarkNamedTupleProtocol(DarkNetworkProtocol[NamedTuple]):

    # Let's actually take advantage of the UTF-8 encoding.
    DELIMITER = "¦"
    NULL = "¨"

    def __init__(self, protocol_format_module):
        self._codec = DarkUtf8StringProtocol()
        self._protocol_format_module = protocol_format_module

    def encode(self, message: NamedTuple) -> bytes:
        raw = self._to_string(message)
        return self._codec.encode(raw)

    def decode(self, data: bytes) -> NamedTuple:
        strings = self._codec.decode(data)
        return [self._from_string(s) for s in strings]

    def _to_string(self, message: NamedTuple) -> str:
        name = type(message).__name__  # keep consistent
        values = []
        for f in message._fields:
            value = getattr(message, f)
            if value is None:
                values.append(self.NULL)
            else:
                values.append(str(value))
        return self.DELIMITER.join([name] + values)

    def _from_string(self, message_string: str) -> NamedTuple:
        parts = message_string.split(self.DELIMITER)
        name, values = parts[0], parts[1:]
        cls: NamedTuple = getattr(self._protocol_format_module, name, None)
        if cls is None:
            raise ValueError(f"Unknown message type: {name}")
        if len(values) != len(cls._fields):
            raise ValueError(f"Field count mismatch for {name}: expected {len(cls._fields)}, got {len(values)}")
        casted = []
        for f, v in zip(cls._fields, values):
            typ = cls.__annotations__[f]
            if v == self.NULL:
                casted.append(None)
            else:
                casted.append(typ(v))
        return cls(*casted)