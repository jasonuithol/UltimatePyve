from typing import Iterable

from dark_libraries.logging import LoggerMixin

#
# It's like a dictionary, but a tiny bit smarter.
#

class Registry[TKey, TValue](LoggerMixin):

    def __init__(self, can_be_empty = False):
        super().__init__()
        self._instances = dict[TKey, TValue]()
        self._can_be_empty = can_be_empty

    def register(self, key: TKey, value: TValue):
        if key in self._instances.keys():
            self.log(f"WARNING: Already have a registered instance for key={key}")
        self._instances[key] = value

    def register_modded_content(self, key: TKey, value: TValue):
        self._instances[key] = value

    def unregister(self, key: TKey):
        assert self._can_be_empty or len(self) > 0, "Must register instances first."
        del self._instances[key]

    def get(self, key: TKey) -> TValue | None:
        assert self._can_be_empty or len(self._instances) > 0, "Must register instances first."
        return self._instances.get(key, None)
  
    def keys(self) -> Iterable[TKey]:
        assert self._can_be_empty or len(self) > 0, "Must register instances first."
        return self._instances.keys()
    
    def values(self) -> Iterable[TValue]:
        assert self._can_be_empty or len(self) > 0, "Must register instances first."
        return self._instances.values()
    
    def items(self) -> Iterable[tuple[TKey, TValue]]:
        assert self._can_be_empty or len(self) > 0, "Must register instances first."
        return self._instances.items()
    
    def clear(self):
        self._instances.clear()

    def __iter__(self) -> Iterable[tuple[TKey, TValue]]:
        assert self._can_be_empty or len(self) > 0, "Must register instances first."
        return self._instances.items()

    def __len__(self) -> int:
        return len(self._instances)    

