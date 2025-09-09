# file: dark_libraries/service_provider.py
import inspect, typing, sys

class ServiceProvider:
    def __init__(self):
        self._instances = {}
        self._mappings = {}

    def _assert_is_class(self, cls, needs_empty_constructor=True):
        if not inspect.isclass(cls):
            raise TypeError(f"cls is not a class object, but instead is an instance of {type(cls)!r}")
        if needs_empty_constructor:
            param_count = len(inspect.signature(cls).parameters)
            if param_count > 0:
                raise TypeError(f"Constructor has {param_count} parameters, needs 0: {cls!r}")

    def _assert_is_instance(self, obj):
        if inspect.isclass(obj):
            raise TypeError(f"obj is not an instance, but instead is a class object ({obj!r})")

    def register(self, cls):
        self._assert_is_class(cls)
        instance = cls()
        self._instances[cls] = instance
        print(f"[DI] Registered {cls.__name__} as new instance")
        return instance

    def register_instance(self, obj, as_type=None):
        self._assert_is_instance(obj)
        if not as_type is None:
            self._assert_is_class(as_type)
        key = as_type or type(obj)
        self._instances[key] = obj
        print(f"[DI] Registered pre-instantiated singleton: {key.__name__}")

    def register_mapping(self, abstract, concrete):
        self._assert_is_class(abstract, needs_empty_constructor=False)
        self._assert_is_class(concrete)
        self.register(concrete)
        self._mappings[abstract] = concrete
        print(f"[DI] Mapped {abstract.__name__} → {concrete.__name__}")

    def _is_property_injectable(self, instance: object, name: str, anno_type, use_logging = True) -> bool:

        if use_logging:
            log = print
        else:
            log = lambda x: None

        # 1. Skip private
        if name.startswith("_"):
            log(f"[DI] Skipping private property: {name}")
            return False

        # 2. Skip pre-initialized
        current_val = getattr(instance, name, None)
        if current_val is not None:
            log(f"[DI] Skipping pre-initialized property: {name} =", f"{current_val!r}"[:100])
            return False

        # 3. Skip non-resolvable.
        dep = self._resolve_type(anno_type)
        if dep is None:
            log(f"[DI] No matching dependency for {anno_type.__name__} (skipped)")
            return False
        
        #
        # PROPERTY IS INJECTABLE
        #
        return True

    def _resolve_type(self, type_) -> typing.Any:
        if type_ in self._instances:
            return self._instances[type_]
        if type_ in self._mappings:
            concrete = self._mappings[type_]
            if concrete not in self._instances:
                self.register(concrete)
            return self._instances[concrete]
        
        # not registered
        return None

    def inject_all(self):
        for instance in self._instances.values():
            cls = instance.__class__
            try:
                annotations = typing.get_type_hints(cls, globalns=sys.modules[cls.__module__].__dict__)
            except NameError as e:
                raise RuntimeError(f"Failed to resolve type hints for {cls.__name__}: {e}")
            for name, anno_type in annotations.items():
                if self._is_property_injectable(instance, name, anno_type):
                    # Resolve and inject
                    dep = self._resolve_type(anno_type)
                    setattr(instance, name, dep)
                    print(f"[DI] Injected {anno_type.__name__} into {instance.__class__.__name__}.{name}")

        for instance in self._instances.values():
            if hasattr(instance, '_after_inject'):
                print(f"[DI] Found _after_inject handler for {instance.__class__.__name__}, invoking...")
                instance._after_inject()

    def resolve(self, type_):
        """Fetch an instance manually, honoring mappings and singletons."""
        # Direct instance
        if type_ in self._instances:
            return self._instances[type_]

        # Abstract → concrete mapping
        if type_ in self._mappings:
            concrete = self._mappings[type_]
            if concrete not in self._instances:
                self.register(concrete)
            return self._instances[concrete]

        raise KeyError(f"No instance or mapping found for {type_.__name__}")

#
# MAIN
#
if __name__ == "__main__":

    #
    # register_singleton() test
    #
    
    provider = ServiceProvider()
    class Demo1:
        pass

    demo1 = Demo1()
    provider.register_instance(demo1)
    provider.inject_all()

    demo1a = provider.resolve(Demo1)

    assert demo1 == demo1a, "register_singleton does not return previously stored instance."

    #
    # register_singleton_factory() test
    #
    class Demo2():
        demo1: Demo1

    provider.register(Demo2)
    provider.inject_all()

    demo2 = provider.resolve(Demo2)
    assert demo1 == demo2.demo1, "previously registered singleton not injected into referencing type."

    #
    # Skip private property test
    #
    class DemoPrivate():
        _private: Demo1
        public: Demo1

    provider.register(DemoPrivate)
    provider.inject_all()

    demo_private = provider.resolve(DemoPrivate)

    assert not hasattr(demo_private, '_private'), "private properties (start with underscore) not being skipped for injection."

    #
    # Skip properties with defaults
    #
    class DemoWithDefault():
        demo1: Demo1 = Demo1()

    provider.register(DemoWithDefault)
    provider.inject_all()

    demo_with_default = provider.resolve(DemoWithDefault)

    assert demo_with_default.demo1 != demo1, "Properties with defaults are having their values being overwritten with injected instances."

    #
    # Skip built-ins
    #
    class TypicalDatabaseRecord():
        str_value: str
        int_value: int
        float_value: float
        bool_value: bool

        list_value: list
        dict_value: dict
        tuple_value: tuple
        set_value: set

    provider.register(TypicalDatabaseRecord)
    provider.inject_all()

    typical = provider.resolve(TypicalDatabaseRecord)

    assert not hasattr(typical, 'str_value'), "strings getting injected - no good."
    assert not hasattr(typical, 'int_value'), "ints getting injected - no good."
    assert not hasattr(typical, 'float_value'), "floats getting injected - no good."
    assert not hasattr(typical, 'bool_value'), "bools getting injected - no good."

    assert not hasattr(typical, 'list_value'), "lists getting injected - no good."
    assert not hasattr(typical, 'dict_value'), "dicts getting injected - no good."
    assert not hasattr(typical, 'tuple_value'), "tuples getting injected - no good."
    assert not hasattr(typical, 'set_value'), "sets getting injected - no good."

    #
    # Circular (preregistered)
    #
    class Demo_Prereg_A():
        demo_b: 'Demo_Prereg_B'

    class Demo_Prereg_B():
        demo_a: 'Demo_Prereg_A'

    provider.register(Demo_Prereg_A)
    provider.register(Demo_Prereg_B)
    provider.inject_all()

    demo_prereg_a = provider.resolve(Demo_Prereg_A)
    demo_prereg_b = provider.resolve(Demo_Prereg_B)

    assert demo_prereg_a.demo_b == demo_prereg_b, "Circular prereg injection failed for demo_prereg_a.demo_b"
    assert demo_prereg_b.demo_a == demo_prereg_a, "Circular prereg injection failed for demo_prereg_b.demo_a"

    #
    # Registering a mapping
    #
    class Superclass():
        pass

    class Subclass(Superclass):
        pass

    provider.register_mapping(Superclass, Subclass)
    provider.inject_all()

    some_subtype_of_syper = provider.resolve(Superclass)

    assert type(some_subtype_of_syper) is Subclass, "Super -> Sub type mapping fails to produce correct resolved instance."

    #
    # Injecting into inherited properties
    #
    class SuperclassProperties():
        demo1: Demo1

    class SubclassProperties(SuperclassProperties):
        pass

    provider.register_mapping(SuperclassProperties, SubclassProperties)
    provider.inject_all()

    sub_type_props = provider.resolve(SuperclassProperties)

    assert sub_type_props.demo1 == demo1, "Super -> Sub type mapping fails to inject inherited properties."

    print("All tests passed.")
