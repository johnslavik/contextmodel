from collections.abc import Callable, Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from functools import cache, partial
from typing import ClassVar


class Context[M: ContextModel, **P]:
    """
    Context. Call it to create a new object.

    >>> from dataclasses import dataclass

    >>> @dataclass
    ... class Foo(ContextModel):
    ...     x: int | None = None

    >>> @context_create(Foo, x=1)
    ... def f() -> None:
    ...     print(context_get(Foo))
    >>> f()
    Foo(x=1)

    >>> with Foo.model_context.create(x=2):
    ...     print(Foo.model_current.x)
    2

    >>> @Foo.model_context.create(x=3)
    ... def f() -> None:
    ...     print(Foo.model_current.x)
    >>> f()
    3

    """

    def __init__(self, model_class: Callable[P, M], variable: ContextVar[M]) -> None:
        self.model_class = model_class
        self.variable = variable

    def get(self) -> M:
        return self.variable.get()

    def set(self, model: M) -> Generator[Token[M]]:
        token = self.variable.set(model)
        try:
            yield token
        finally:
            token.var.reset(token)

    @contextmanager
    def create(self, *args: P.args, **kwargs: P.kwargs) -> Generator[Token[M]]:
        return self.set(self.model_class(*args, **kwargs))


def context_get[M: ContextModel](model_class: type[M]) -> M:
    """
    Get the current context model instance.

    >>> from dataclasses import dataclass, field

    >>> @dataclass
    ... class Foo(ContextModel):
    ...     x: int = 1

    >>> with Foo.model_context.create(x=2):
    ...     print(context_get(Foo))
    Foo(x=2)
    """
    return context_of(model_class).get()


def future_context_get[M: ContextModel](model_class: type[M]) -> Callable[[], M]:
    """
    Return a callback to return a value from context. Useful as "factories".

    >>> from dataclasses import dataclass, field

    >>> @dataclass
    ... class Foo(ContextModel):
    ...     x: int = 1

    >>> @dataclass
    ... class MyData:
    ...     foo: Foo = field(default_factory=future_context_get(Foo))

    >>> MyData(foo=Foo())
    MyData(foo=Foo(x=1))

    >>> with Foo.model_context.create(x=2):
    ...     print(MyData())
    MyData(foo=Foo(x=2))

    """
    return partial(context_get, model_class)


@cache
def context_of[M: ContextModel, **P](
    model_class: Callable[P, M],
) -> Context[M, P]:
    auto_name = getattr(model_class, "__name__", format(model_class))
    return Context(model_class=model_class, variable=ContextVar[M](auto_name))


@contextmanager
def context_create[**P, M: Context](
    model_class: Callable[P, M],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> Generator[M]:
    context = context_of(model_class)
    return context.set(context.model_class(*args, **kwargs))


@contextmanager
def context_set[**P, M: Context](
    model_class: Callable[P, M],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> Generator[M]:
    context = context_of(model_class)
    return context.set(context.model_class(*args, **kwargs))


class _ContextGetter:
    def __get__[M: ContextModel, **P](
        self,
        instance: M | None,
        owner: Callable[P, M],
    ) -> Context[M, P]:
        return context_of(owner or type(instance))


class _ModelGetter:
    def __get__[M: ContextModel, **P](
        self,
        instance: M | None,
        owner: Callable[P, M],
    ) -> M:
        return context_get(owner if instance is None else instance)  # type: ignore[invalid-argument-type]


class ContextModel:
    model_context: ClassVar[_ContextGetter] = _ContextGetter()
    model_current: ClassVar[_ModelGetter] = _ModelGetter()
