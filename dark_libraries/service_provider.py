# file: dark_libraries/service_provider.py
import inspect, typing, sys

from dark_libraries.logging import LoggerMixin

class ServiceProvider(LoggerMixin):

    _instance: typing.Self = None

    @classmethod
    def get_provider(cls):
        if cls._instance is None:
            return cls()
        return cls._instance

    def __init__(self):
        assert self.__class__._instance is None, "Cannot instantiate multiple ServiceProvider roots."

        super().__init__()
        self._instances = {}
        self._mappings = {}
        self.__class__._instance = self

    def _assert_is_class(self, cls, needs_empty_constructor=True):
        assert inspect.isclass(cls), f"cls is not a class object, but instead is an instance of {type(cls)!r}"

        if needs_empty_constructor:
            param_count = len(inspect.signature(cls).parameters)
            assert param_count == 0, f"Constructor has {param_count} parameters, needs 0: {cls!r}"

    def _assert_is_instance(self, obj):
        assert not inspect.isclass(obj), f"obj is not an instance, but instead is a class object ({obj!r})"

    def register(self, cls):
        self._assert_is_class(cls)
        instance = cls()
        self._instances[cls] = instance
        self.log(f"DEBUG: Registered {cls.__name__} as new instance")
        return instance

    def register_instance(self, obj, as_type=None):
        self._assert_is_instance(obj)
        if not as_type is None:
            self._assert_is_class(as_type)
        key = as_type or type(obj)
        self._instances[key] = obj
        self.log(f"DEBUG: Registered pre-instantiated singleton: {key.__name__}")

    def register_mapping(self, abstract, concrete):
        self._assert_is_class(abstract, needs_empty_constructor=False)
        self._assert_is_class(concrete)
        self.register(concrete)
        self._mappings[abstract] = concrete
        self.log(f"DEBUG: Mapped {abstract.__name__} → {concrete.__name__}")

    def _is_property_injectable(self, instance: object, name: str, anno_type, use_logging = True) -> bool:

        if use_logging:
            log = self.log
        else:
            log = lambda x: None

        # 1. Skip private
        if name.startswith("_"):
            log(f"Skipping private property: {instance.__class__.__name__}.{name}")
            return False

        # 2. Skip pre-initialized
        current_val = getattr(instance, name, None)
        if current_val is not None:
            log(f"Skipping pre-initialized property: {instance.__class__.__name__}.{name} = {current_val!r}"[:100])
            return False

        # 3. Skip non-resolvable.
        dep = self._resolve_type(anno_type)
        if dep is None:
            log(f"WARNING: No matching dependency for {instance.__class__.__name__}.{name} on type {anno_type.__name__} (skipped)")
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
                    self.log(f"DEBUG: Injected {anno_type.__name__} into {instance.__class__.__name__}.{name}")

        self.log("Injection complete. Calling _after_inject handlers.")
        for instance in self._instances.values():
            if hasattr(instance, '_after_inject'):
                self.log(f"DEBUG: Found _after_inject handler for {instance.__class__.__name__}, invoking...")
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
