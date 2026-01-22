from collections.abc import Callable, Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import cache
from typing import Any, ClassVar, dataclass_transform


class Context[C, **P]:
    """
    Internal class to create and register new current instance.

    Subclass [`ContextClass`][] to make use of it.

    >>> class Foo(ContextClass):
    ...     x: int | None = None

    >>> with Foo.context(x=1):
    ...     print(Foo.current.x)
    1
    """

    def __init__(self, constructor: Callable[P, C], contextvar: ContextVar[C]) -> None:
        self.constructor = constructor
        self.contextvar = contextvar

    @contextmanager
    def __call__(self, *__never__: P.args, **kwargs: P.kwargs) -> Generator[C]:
        value = self.constructor(**kwargs)
        token = self.contextvar.set(value)
        try:
            yield value
        finally:
            token.var.reset(token)


class _ContextGetter:
    def __get__[T, **P](self, instance: T, owner: Callable[P, T]) -> Context[T, P]:
        return context_of(owner or type(instance))


class _CurrentInstanceGetter:
    def __get__[T: ContextClass, **P](
        self,
        instance: T | None,
        owner: Callable[P, T],
    ) -> T:
        lens = owner if instance is None else instance
        return lens.context.contextvar.get()


@cache
def context_of[T, **P](context_class: Callable[P, T]) -> Context[T, P]:
    return Context(context_class, ContextVar[T](context_class.__name__))


@dataclass_transform(kw_only_default=True)
class ContextClass:
    context: ClassVar[_ContextGetter] = _ContextGetter()
    current: ClassVar[_CurrentInstanceGetter] = _CurrentInstanceGetter()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        kwargs["kw_only"] = True
        dataclass(cls, **kwargs)
