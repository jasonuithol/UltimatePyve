from typing import Protocol

from maps import U5Map

class InteractableFactory(Protocol):
    def load_level(self, factory_registry: 'InteractableFactoryRegistry', u5map: U5Map, level_index: int):
        ...
