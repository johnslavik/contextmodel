# contextmodel
Alternative interface to context variables for practical scenarios.

```pycon
>>> from contextmodel import context_get, context_set
>>> from dataclasses import dataclass

>>> @dataclass
... class Foo:
...     x: int | None = None

>>> @context_set(Foo(x=1))
... def f() -> None:
...     print(context_get(Foo))
>>> f()
Foo(x=1)

>>> from contextmodel import ContextAPIGetter, ModelGetter
>>> from typing import ClassVar

>>> @dataclass
... class Foo:
...     context = ContextAPIGetter()
...     current = ModelGetter()
...     x: int | None = None

>>> with Foo.context.init(x=2):
...     print(Foo.context.get())
Foo(x=2)

>>> @Foo.context.init(x=3)
... def f() -> None:
...     print(context_get(Foo))
>>> f()
Foo(x=3)

>>> def oops() -> None:
...     print(Foo.current)
>>> oops()
Traceback (most recent call last):
  ...
LookupError: expected a context_set(Foo(...)) prior to this call

```

Works with type hints.
