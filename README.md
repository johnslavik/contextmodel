# contextmodel
Alternative interface to context variables for practical scenarios.

```pycon
>>> from contextmodel import ContextModel, context_create, context_get
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


```

Works with type hints:

<img width="821" height="454" alt="image" src="https://github.com/user-attachments/assets/6c4f5b4b-48b5-4807-a6aa-bf9cd6b8e3e4" />
