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

>>> from contextmodel import ContextAPIGetter
>>> from typing import ClassVar

>>> @dataclass
... class Foo:
...     context: ClassVar[ContextAPIGetter] = ContextAPIGetter()
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
...     print(context_get(Foo))
>>> oops()
Traceback (most recent call last):
  ...
LookupError: expected a context_set(Foo(...)) prior to this call

```

Works with type hints:

<center>

<img width="630" height="408" alt="image" src="https://github.com/user-attachments/assets/a482bcc7-88f3-4002-a34d-37c52c9fa725" />

</center>
