from collections.abc import Callable, Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from functools import cache, partial
from typing import ClassVar


class Context[T: ContextLocal, **P]:
    """
    Internal class to create and register new current instance.

    Use [`context_of`][] or subclass [`ContextLocal`][] to make use of it.

    >>> from dataclasses import dataclass

    >>> @dataclass
    ... class Foo(ContextLocal):
    ...     x: int | None = None

    >>> @enter(Foo, x=1)
    ... def f() -> None:
    ...     print(current(Foo))
    >>> f()
    Foo(x=1)

    >>> with Foo.context(x=2):
    ...     print(Foo.current.x)
    2

    >>> @Foo.context(x=3)
    ... def f() -> None:
    ...     print(Foo.current.x)
    >>> f()
    3

    """

    def __init__(self, constructor: Callable[P, T], contextvar: ContextVar[T]) -> None:
        self.constructor = constructor
        self.contextvar = contextvar

    def _cm(self, *args: P.args, **kwargs: P.kwargs) -> Generator[Token[T]]:
        value = self.constructor(*args, **kwargs)
        token = self.contextvar.set(value)
        try:
            yield token
        finally:
            token.var.reset(token)

    @contextmanager
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Generator[Token[T]]:
        return self._cm(*args, **kwargs)


class _ContextGetter:
    def __get__[T: ContextLocal, **P](
        self,
        instance: T | None,
        owner: Callable[P, T],
    ) -> Context[T, P]:
        return context_of(owner or type(instance))


class _CurrentInstanceGetter:
    def __get__[T: ContextLocal, **P](
        self,
        instance: T | None,
        owner: Callable[P, T],
    ) -> T:
        return current(owner if instance is None else instance)  # type: ignore[invalid-argument-type]


def current[T: ContextLocal](context_class: type[T]) -> T:
    return context_of(context_class).contextvar.get()


def from_context[T: ContextLocal](context_class: type[T]) -> Callable[[], T]:
    return partial(current, context_class)


@cache
def context_of[T: ContextLocal, **P](context_class: Callable[P, T]) -> Context[T, P]:
    auto_name = getattr(context_class, "__name__", format(context_class))
    return Context(context_class, ContextVar[T](auto_name))


@contextmanager
def enter[**P, T: Context](
    context_class: Callable[P, T],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> Generator[T]:
    return context_of(context_class)._cm(*args, **kwargs)


class ContextLocal:
    context: ClassVar[_ContextGetter] = _ContextGetter()
    current: ClassVar[_CurrentInstanceGetter] = _CurrentInstanceGetter()


# Use by the preferred name.
ContextClass = ContextLocal
