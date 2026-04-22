import pytest

from dark_libraries.service_provider import ServiceProvider


# Module-level helper classes — required for forward-ref resolution
# (typing.get_type_hints reads the *defining module's* globals).

class Demo1:
    pass


class Demo2:
    demo1: Demo1


class DemoPrivate:
    _private: Demo1
    public: Demo1


class DemoWithDefault:
    demo1: Demo1 = Demo1()


class TypicalDatabaseRecord:
    str_value: str
    int_value: int
    float_value: float
    bool_value: bool
    list_value: list
    dict_value: dict
    tuple_value: tuple
    set_value: set


class Demo_Prereg_A:
    demo_b: "Demo_Prereg_B"


class Demo_Prereg_B:
    demo_a: "Demo_Prereg_A"


class Superclass:
    pass


class Subclass(Superclass):
    pass


class SuperclassProperties:
    demo1: Demo1


class SubclassProperties(SuperclassProperties):
    pass


@pytest.fixture
def provider():
    # ServiceProvider asserts singleton in __init__; reset before & after each test.
    ServiceProvider._instance = None
    p = ServiceProvider()
    yield p
    ServiceProvider._instance = None


def test_register_instance_round_trip(provider):
    demo = Demo1()
    provider.register_instance(demo)
    provider.inject_all()
    assert provider.resolve(Demo1) is demo


def test_factory_injects_existing_singleton(provider):
    demo = Demo1()
    provider.register_instance(demo)
    provider.register(Demo2)
    provider.inject_all()
    assert provider.resolve(Demo2).demo1 is demo


def test_private_properties_are_skipped(provider):
    provider.register_instance(Demo1())
    provider.register(DemoPrivate)
    provider.inject_all()
    assert not hasattr(provider.resolve(DemoPrivate), "_private")


def test_pre_initialized_properties_are_not_overwritten(provider):
    demo = Demo1()
    provider.register_instance(demo)
    provider.register(DemoWithDefault)
    provider.inject_all()
    # The pre-existing default Demo1() instance must survive injection.
    assert provider.resolve(DemoWithDefault).demo1 is not demo


def test_builtin_typed_properties_are_skipped(provider):
    provider.register(TypicalDatabaseRecord)
    provider.inject_all()
    typical = provider.resolve(TypicalDatabaseRecord)
    for attr in (
        "str_value", "int_value", "float_value", "bool_value",
        "list_value", "dict_value", "tuple_value", "set_value",
    ):
        assert not hasattr(typical, attr), f"{attr} should not have been injected"


def test_circular_preregistered_injection(provider):
    provider.register(Demo_Prereg_A)
    provider.register(Demo_Prereg_B)
    provider.inject_all()
    a = provider.resolve(Demo_Prereg_A)
    b = provider.resolve(Demo_Prereg_B)
    assert a.demo_b is b
    assert b.demo_a is a


def test_register_mapping_resolves_to_concrete_subtype(provider):
    provider.register_mapping(Superclass, Subclass)
    provider.inject_all()
    assert type(provider.resolve(Superclass)) is Subclass


def test_register_mapping_injects_inherited_properties(provider):
    demo = Demo1()
    provider.register_instance(demo)
    provider.register_mapping(SuperclassProperties, SubclassProperties)
    provider.inject_all()
    assert provider.resolve(SuperclassProperties).demo1 is demo
