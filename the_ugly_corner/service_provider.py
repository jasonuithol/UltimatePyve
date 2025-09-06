# file: dark_libraries/service_provider.py

import inspect
import sys
from typing import Any, Callable, Tuple, get_type_hints

class ServiceProvider:

    BANNED_CLASSES = [list, dict, set, tuple]

    def __init__(self, auto_resolve: bool = True):
        self.auto_resolve = auto_resolve
        self._singleton_registry: dict[str, object] = dict()
        self._singleton_factories: dict[str, Tuple[type, Callable]] = dict()
        print(f"ServiceProvider auto_resolve = {self.auto_resolve}")

    def _get_preregistered_singleton(self, cls: type) -> Any:
        cls_key = self._get_key(cls)
        return self._singleton_registry[cls_key]

    def _create_singleton_from_factory(self, cls: type, constructor: Callable = None) -> Any:
        cls_key = self._get_key(cls)

        try:
            # Check if an instance, or create a new one if it doesn't exist
            instance = self._singleton_registry.get(cls_key)
            if instance is None:
                if constructor is None:
                    constructor = cls.__init__
                if inspect.isclass(constructor):
                    concrete_cls = constructor
                    constructor = concrete_cls.__init__
                else:
                    concrete_cls = cls

                instance = concrete_cls.__new__(concrete_cls)
                self.register_singleton(instance)

            # Resolve all type annotations, including forward references (e.g. string-based type annotations), 
            # of the constructor e.g. 
            # 
            # __init__(self, normally_reffed: NormalReference, forward_reffed: 'ForwardReference')
            #
            resolved_type_hints = get_type_hints(constructor, globalns=sys.modules[cls.__module__].__dict__)

            constructor_signature = inspect.signature(constructor)
            params = {}

            # Try to resolve all the parameters in the constructor for "instance"
            for param_name in constructor_signature.parameters.keys():
                if param_name == "self":
                    continue
                
                # Obtain the type of the parameter
                dependent_type = resolved_type_hints.get(param_name, None)
                if dependent_type is None:
                    raise TypeError(f"No type annotation for parameter '{param_name}' in {constructor}")

                param_default = constructor_signature.parameters[param_name].default
                if param_default != inspect.Parameter.empty:
                    params[param_name] = param_default
                else:
                    # Use that parameter type to recursively construct/retrieve a parameter value.
                    dependent_singleton_instance = self.get(dependent_type)
                    params[param_name] = dependent_singleton_instance

            # Now we can construct "instance". We do this by manually calling __init__ on it
            # i.e.  __init__(instance, **params).  This means we keep our special, specific, particular instance
            # and not spawn a new one (which would happen if we had called "instance = concrete_cls(**params)")
            constructor(instance, **params)
            
            return instance

        except Exception as e:
            raise TypeError(f"Cannot construct {cls}: {e}")


    def _get_key(self, cls: type) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"
    
    def _get_factory_name(self, constructor: Callable) -> str:
        if hasattr(constructor, "__qualname__"):
            func_name = f"{constructor.__module__}.{constructor.__qualname__}"
        else:
            func_name = repr(constructor)
        return func_name

    def register_singleton(self, obj: object) -> None:

        if type(obj) in ServiceProvider.BANNED_CLASSES:
            raise TypeError(
                f"Refusing to register singleton for built-in type {type(obj).__name__}. "
                "Pass it after construction or wrap it in a subtype.  "
                "Remember to construct your subtype with the subtype constructor !"
            )
        
        cls_key = self._get_key(type(obj))

        # TODO: Remove
        print(f"REGISTER_SINGLETON {type(obj)} key={cls_key} id={hex(id(obj))}")

        self._singleton_registry[cls_key] = obj

    def register_singleton_factory(self, cls: type, constructor: Callable = None) -> None:

        if constructor in ServiceProvider.BANNED_CLASSES:
            raise TypeError(
                f"Refusing to register factory of built-in type {constructor}. "
                "Pass it after construction or wrap it in a subtype."
            )
        
        cls_key = self._get_key(cls)
        factory_name = self._get_factory_name(constructor)

        # TODO: Remove
        print(f"REGISTER_FACTORY {type(constructor)} key={cls_key} factory_name={factory_name}")

        if constructor == None:
            constructor = cls.__init__
        self._singleton_factories[cls_key] = constructor

    def get(self, cls: type) -> Any:

        if cls in ServiceProvider.BANNED_CLASSES:
            raise TypeError(
                f"Refusing to resolve built-in type {cls.__name__}. "
                "Pass it after construction or wrap it in a subtype."
            )

        cls_key = self._get_key(cls)

        # TODO: Remove
        print(f"GET {cls} key={cls_key} in registry? {cls_key in self._singleton_registry}")

        try:
            if cls_key in self._singleton_registry.keys():
                return self._get_preregistered_singleton(cls)
            elif cls_key in self._singleton_factories.keys():
                return self._create_singleton_from_factory(cls)
            elif self.auto_resolve:
                default_constructor = cls.__init__
                return self._create_singleton_from_factory(cls, default_constructor)
            raise KeyError(f"Unregistered type {cls}")

        except Exception as e:            
            self.print_registry()
            raise e
    
    def print_registry(self) -> None:
        print("REGISTRIES: singletons")
        for cls_key, obj in self._singleton_registry.items():
            print(f"{cls_key} -> {hex(id(obj))}")
        print("REGISTRIES: factories")
        for cls_key, func in self._singleton_factories.items():
            factory_name = self._get_factory_name(func)
            print(f"{cls_key} -> {factory_name}")

#
# MAIN
#
if __name__ == "__main__":

    #
    # register_singleton() test
    #
    
    class Demo1:
        pass

    demo1 = Demo1()
    provider = ServiceProvider(auto_resolve=False)
    provider.register_singleton(demo1)

    demo1a = provider.get(Demo1)

    assert demo1 == demo1a, "register_singleton does not return previously stored instances."

    #
    # register_singleton_factory() test
    #
    class Demo2:
        def __init__(self, demo1: Demo1):
            self.demo1 = demo1

    provider.register_singleton_factory(Demo2)
    demo2 = provider.get(Demo2)

    #
    # auto resolve test
    #

    provider.auto_resolve = True
    print("Provider auto_resolve turned ON.")

    class Demo3:
        def __init__(self, demo1: Demo1, demo2: Demo2):
            self.demo1 = demo1
            self.demo2 = demo2

    # Demo3 was never registered.
    demo3 = provider.get(Demo3)

    class Demo4:
        def __init__(self, demo3: Demo3):
            self.demo3 = demo3

    # Demo4 was never registered, and also references Demo3,
    # which was never EXPLICITLY registered, but by now should 
    # be automatically registered. 

    demo4 = provider.get(Demo4)

    assert demo3 == demo4.demo3

    #
    # string-style type annotation test
    #
    class StringReferencer:
        def __init__(self, demo1: 'Demo1'):
            self.demo1 = demo1

    string_referencer = provider.get(StringReferencer)

    assert string_referencer.demo1 == demo1

    #
    # auto-resolve parameter references (i.e. recursion tests)
    #

    class NeverSeenMeUntilBeingReferenced:
        def __init__(self, demo1: Demo1):
            self.demo1 = demo1

    class BackwardlyReferencingClass:
        def __init__(self, never_seen: NeverSeenMeUntilBeingReferenced):
            self.never_seen = never_seen

    backwardly = provider.get(BackwardlyReferencingClass)
    never_seen = provider.get(NeverSeenMeUntilBeingReferenced)

    assert backwardly.never_seen == never_seen

    class HereIAm:
        def __init__(self, forward_reffed: 'ForwardReference'):
            self.forward_reffed = forward_reffed

    class ForwardReference:
        def __init__(self, demo1: Demo1):
            self.demo1 = demo1

    here_i_am = provider.get(HereIAm)
    forward_reffed = provider.get(ForwardReference)

    provider.print_registry()
    print(f"here_i_am.forward_reffed={here_i_am.forward_reffed!r}")
    print(f"forward_reffed={forward_reffed!r}")

    assert here_i_am.forward_reffed == forward_reffed


#    exit() # the next test is an infinite loop that crashes the stack, bail here until forward refs work.

    #
    # Circular reference test.
    #
    class Demo5:
        def __init__(self, demo6: 'Demo6'):
            self.demo6 = demo6

    class Demo6:
        def __init__(self, demo5: 'Demo5'):
            self.demo5 = demo5

    demo5 = provider.get(Demo5)
    demo6 = provider.get(Demo6)

    assert demo5.demo6 is demo6
    assert demo6.demo5 is demo5

    print("All tests passed.")
