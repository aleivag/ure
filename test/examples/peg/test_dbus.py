from typing import Any, List, Tuple

import pytest

from ure import by_name
from ure.peg import Parser

parser = Parser()

parser.expr.update(
    {
        # base
        "int": ("/[nqiyuxth]/", lambda *_: int),
        "bool": ("/b/", lambda *_: bool),
        "bytes": ("/[sog]/", lambda *_: bytes),
        "float": ("/d/", lambda *_: float),
        "var": ("/v/", lambda *_: Any),
        # simple
        "simple": "int | bool | bytes | float | var",
        # complex
        "array": (" 'a'! & @inner:(dbus) ", by_name(lambda inner: List[inner])),
        "tuple": (
            r" '\(' & @inner:(dbus)+  & '\)' ",
            by_name(lambda inner: Tuple[tuple(inner)]),
        ),
        "dbus": "array | tuple | simple",
    }
)


dbus = parser.compile("dbus")


@pytest.mark.parametrize(
    "expr,res",
    [
        ("(sbsv)", Tuple[bytes, bool, bytes, Any]),
        ("a(asvn(uu))", List[Tuple[List[bytes], Any, int, Tuple[int, int]]]),
        ("v", Any),
        ("as", List[bytes]),
        ("(asb)", Tuple[List[bytes], bool]),
    ],
)
def test_dbus(expr, res):
    assert dbus.parse(expr).result == res
