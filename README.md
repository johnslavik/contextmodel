# contextclass
Alternative interface to context variables for practical scenarios.

```pycon
>>> from contextclass import ContextLocal, enter, current
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

```

Works with type hints:

<img width="881" height="182" alt="image" src="https://github.com/user-attachments/assets/abeb517e-36ae-4cf7-8c6f-a1849c6cefde" />
<img width="925" height="216" alt="image" src="https://github.com/user-attachments/assets/a6a2bbe5-00d9-45b6-8603-431c1f6024f0" />
<img width="833" height="252" alt="image" src="https://github.com/user-attachments/assets/60bf954b-5a05-4b24-9bc1-550597b26c57" />
