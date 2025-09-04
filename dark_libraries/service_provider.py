# file: composition.py

import inspect
from typing import Callable, Tuple

class ServiceProvider:
    def __init__(self, allow_auto: bool = True):
        self.allow_auto = allow_auto
        self._singleton_registry: dict[str, object] = dict()
        self._singleton_factories: dict[str, Tuple[type, Callable]] = dict()
        print(f"ServiceProvider auto-resolve = {self.allow_auto}")

    def _get_preregistered_singleton(self, cls: type) -> object:
        cls_key = self._get_key(cls)
        return self._singleton_registry[cls_key]

    def _create_singleton_from_factory(self, cls: type, constructor: Callable = None) -> object:
        cls_key = self._get_key(cls)
        if constructor is None:
            constructor = self._singleton_factories[cls_key]
        try:
            sig = inspect.signature(constructor)
            params = {}

            for name, param in sig.parameters.items():
                if name == "self":  # skip instance reference
                    continue

                # Here you decide how to resolve each parameter
                # For example, by type annotation:
                if param.annotation is not inspect._empty:
                    dep = self.get(param.annotation)
                    params[name] = dep
                else:
                    raise TypeError(f"No type annotation for parameter '{name}' in {constructor}")

            instance = cls(**params)

            # Register the instance for subsequent calls.
            self.register_singleton(instance)

            return instance

        except Exception as e:
            raise TypeError(f"Cannot construct {cls}: {e}")

    def _get_key(self, cls: type):
        return f"{cls.__module__}.{cls.__qualname__}"

    def register_singleton(self, obj: object):
        cls_key = self._get_key(type(obj))
        self._singleton_registry[cls_key] = obj

    def register_singleton_factory(self, cls: type, constructor: Callable = None):
        cls_key = self._get_key(cls)
        if constructor == None:
            constructor = cls.__init__
        self._singleton_factories[cls_key] = constructor

    def get(self, cls: type):
        cls_key = self._get_key(cls)
        try:
            if cls_key in self._singleton_registry.keys():
                return self._get_preregistered_singleton(cls)
            elif cls_key in self._singleton_factories.keys():
                return self._create_singleton_from_factory(cls)
            elif self.allow_auto:
                default_constructor = cls.__init__
                return self._create_singleton_from_factory(cls, default_constructor)
            raise KeyError(f"Unregistered type {cls}")

        except Exception as e:            
            self.print_registry()
            raise e
    
    def print_registry(self):
        print("REGISTRIES: singletons")
        print(self._singleton_registry)
        print("REGISTRIES: factories")
        print(self._singleton_factories)

#
# MAIN
#
if __name__ == "__main__":
    class Demo1:
        pass

    class Demo2:
        def __init__(self, demo1: Demo1):
            self.demo1 = Demo1

    demo1 = Demo1()
    provider = ServiceProvider(allow_auto=False)
    provider.register_singleton(demo1)

    demo1a = provider.get(Demo1)
    assert demo1 == demo1a, "register_singleton does not return previously stored instances."

    provider.register_singleton_factory(Demo2)
    demo2 = provider.get(Demo2)

    provider.allow_auto = True
    print("Provider auto resolve turned ON.")

    class Demo3:
        def __init__(self, demo1: Demo1, demo2: Demo2):
            self.demo1 = demo1
            self.demo2 = demo2

    demo3 = provider.get(Demo3)

    class Demo4:
        def __init__(self, demo3: Demo3):
            self.demo3 = demo3

    demo4 = provider.get(Demo4)

    assert demo3 == demo4.demo3

    print("All tests passed.")
