"""
Uses Python descriptors to add mixin attributes that are able to have default values.
"""
from typing import Generic, TypeVar, Type, Optional, Callable, overload, Union, Literal
import weakref

T = TypeVar("T")
U = TypeVar("U")
TObject = TypeVar("TObject", bound=object)


class AttributeHandler(Generic[TObject, T]):
    def __init__(self, default_value: T) -> None:
        self.__name: Optional[str] = None
        self.__default_value: T = default_value
        self.__variable: dict[int, T] = {}

    def _get_id(self, obj: TObject) -> int:
        return id(obj)

    def _add_destructor_hooks(self, obj: TObject) -> None:
        def cleanup() -> None:
            del self.__variable[self._get_id(obj)]

        weakref.finalize(obj, cleanup)

    def __contains__(self, obj: TObject) -> bool:
        return self._get_id(obj) in self.__variable

    def __getitem__(self, obj: TObject) -> T:
        return self.__variable.get(self._get_id(obj), self.__default_value)

    def __setitem__(self, obj: TObject, value: T) -> None:
        if obj not in self:
            self._add_destructor_hooks(obj)
        self.__variable[self._get_id(obj)] = value

    def __set_name__(self, owner: Type[TObject], name: str) -> None:
        self.__name = name

    def __get__(self, obj: TObject, obj_type: Optional[Type[TObject]]) -> T:
        return self[obj]

    def __set__(self, obj: TObject, value: T) -> None:
        self[obj] = value


class MixinProperty(Generic[T]):
    def __init__(self, default_value: T) -> None:
        self.__default_value = default_value

    def __call__(
        self, to_be_decorated: Callable[[TObject], T]
    ) -> AttributeHandler[TObject, T]:
        handler: AttributeHandler[TObject, T] = AttributeHandler(self.__default_value)
        return handler


class OptionalMixinProperty(Generic[T]):
    def __init__(self, default_value: Optional[T] = None) -> None:
        self.__default_value = default_value

    def __call__(
        self, to_be_decorated: Callable[[TObject], Optional[T]]
    ) -> AttributeHandler[TObject, Optional[T]]:
        handler: AttributeHandler[TObject, Optional[T]] = AttributeHandler(
            self.__default_value
        )
        return handler


def mixin_property(default_value: T) -> MixinProperty[T]:
    assert default_value is not None
    return MixinProperty(default_value)


def optional_mixin_property(
    default_value: Optional[T] = None,
) -> OptionalMixinProperty[T]:
    return OptionalMixinProperty(default_value)


TestMixinType = TypeVar("TestMixinType", bound="TestMixin")


class TestMixin:
    @optional_mixin_property()
    def _x(self) -> Optional[int]:
        ...

    @optional_mixin_property(1)
    def _y(self) -> Optional[int]:
        ...

    @mixin_property(3)
    def _z(self) -> int:
        ...

    def set_z(self: TestMixinType, z: int) -> TestMixinType:
        self._z = z
        return self

    def get_z(self) -> int:
        return self._z


class Base(TestMixin):
    ...


class OtherBase(TestMixin):
    def set_z(self, z: int) -> "OtherBase":
        self._z = z + 1
        return self


def im_some_function() -> None:
    import gc

    b = Base()
    print(b.get_z())
    b = b.set_z(10)
    print(b.get_z())
    del b
    print("deleted z")
    gc.collect()


if __name__ == "__main__":
    im_some_function()
    b = OtherBase()
    print(b._y)
    b._y = 34
    print(b._y)
