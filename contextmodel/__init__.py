from collections.abc import Callable
from contextlib import ContextDecorator
from contextvars import ContextVar, Token
from functools import cache, partial
from typing import ClassVar, Self, overload


class ReusableContextLifecycle[M](ContextDecorator):
    def __init__(self, setter: Callable[[], Token[M]]) -> None:
        self._setter = setter
        self._token = self._setter()

    def __enter__(self) -> Token[M]:
        if self._token is None:
            self._token = self._setter()
        return self._token

    def __exit__(self, *exc_info: object) -> None:
        self.reset()

    def reset(self) -> None:
        if self._token is None:
            return
        self._token.var.reset(self._token)
        self._token = None


class Context[M, **P]:
    global_cache: ClassVar[dict[object, "Context"]] = {}

    def __init__(self, model_class: Callable[P, M], variable: ContextVar[M]) -> None:
        self.model_class = model_class
        self.variable = variable

    def get_or_raise(self) -> M:
        get = self.variable.get
        try:
            return get()
        except LookupError:
            class_name = self.model_class.__qualname__  # type: ignore[possibly-missing-attribute]
            msg = f"expected a context_set({class_name}(...)) prior to this call"
            raise LookupError(msg) from None

    def set(self, model: M) -> ReusableContextLifecycle[M]:
        return ReusableContextLifecycle(partial(ContextVar.set, self.variable, model))

    def create_api(self) -> "ContextAPI[M, P]":
        return CachedContextAPI(self)

    @staticmethod
    def generate_variable_name(model_class: type[M]) -> str:
        return model_class.__qualname__

    @overload
    @classmethod
    def for_class(
        cls, model_class: Callable[P, M], *, check_cache: bool = False
    ) -> Self: ...
    @overload
    @classmethod
    def for_class(
        cls, model_class: Callable[P, M], *, check_cache: bool = True
    ) -> "Context[M, P] | Self": ...

    @classmethod
    def for_class(
        cls,
        model_class: Callable[P, M],
        *,
        check_cache: bool = True,
    ) -> "Context[M, P] | Self":
        if check_cache:
            cached = cls.global_cache.get(model_class)
            if cached is not None:
                return cached
        variable_name = cls.generate_variable_name(model_class)  # type: ignore[invalid-argument-type]
        new_context = cls(model_class, ContextVar(variable_name))
        cls.global_cache[model_class] = new_context
        return new_context


class ContextAPI[M, **P]:
    def __init__(self, manager: Context[M, P]) -> None:
        self.manager = manager

    def get(self) -> M:
        return self.manager.get_or_raise()

    def set(self, model: M) -> ReusableContextLifecycle[M]:
        return self.manager.set(model)

    def init(self, /, *args: P.args, **kwargs: P.kwargs) -> ReusableContextLifecycle[M]:
        return self.manager.set(self.manager.model_class(*args, **kwargs))


# Unbounded cache (one API per one manager) to avoid unnecessary allocations.
CachedContextAPI = cache(ContextAPI)


def context_get[M](model_class: type[M], context_class: type[Context] = Context) -> M:
    """Get the current context model instance."""
    return context_class.for_class(model_class, check_cache=True).get_or_raise()


def future_context_get[M](model_class: type[M]) -> Callable[[], M]:
    """Return a callback to return a value from context. Useful as "factories"."""
    return partial(context_get, model_class)


def context_set[M](
    model: M,
    context_class: type[Context] = Context,
) -> ReusableContextLifecycle[M]:
    context = context_class.for_class(model.__class__, check_cache=True)
    return context.set(model)


class ContextAPIGetter:
    def __call__[M, **P](self, model_class: Callable[P, M]) -> ContextAPI[M, P]:
        return self.__get__(None, model_class)

    def __get__[M, **P](self, _: M | None, owner: Callable[P, M]) -> ContextAPI[M, P]:
        return Context.for_class(owner, check_cache=True).create_api()


class ModelGetter:
    def __call__[M, **P](self, model_class: type[M]) -> M:
        return self.__get__(None, model_class)

    def __get__[M](self, _: M | None, owner: type[M]) -> M:
        return context_get(owner)


class WithContextAttribute:
    """A descriptor-based API to avoid importing this package at user site."""

    context: ClassVar[ContextAPIGetter] = ContextAPIGetter()
