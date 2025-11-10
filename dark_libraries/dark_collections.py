from threading import Lock

class LockedSet[TItem]:
    def __init__(self):
        self._data = set[TItem]()
        self._lock = Lock()

    def add(self, item: TItem):
        with self._lock:
            self._data.add(item)

    def remove(self, item: TItem):
        with self._lock:
            self._data.remove(item)

    def snapshot(self) -> set[TItem]:
        with self._lock:
            return set[TItem](self._data)  # Safe copy for iteration


class LockedDict[TKey, TValue]:
    def __init__(self):
        self._data = dict[TKey, TValue]()
        self._lock = Lock()

    def __setitem__(self, key: TKey, value: TValue):
        with self._lock:
            self._data[key] = value

    def __getitem__(self, key: TKey) -> TValue:
        with self._lock:
            return self._data[key]
        
    def __delitem__(self, key: TKey):
        with self._lock:
            del self._data[key]

    def get(self, key: TKey, default_value: TValue = None):
        with self._lock:
            return self._data.get(key, default_value)

    def snapshot(self) -> dict[TKey, TValue]:
        with self._lock:
            return dict[TKey, TValue](self._data)  # Safe copy for iteration
