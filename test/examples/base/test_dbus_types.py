from typing import Any, List, Tuple

import pytest

from ure import Base, Ignore, MatchAll, MatchFirst, MatchNtoM, Result, Wrap, regex

_int = "nqiyuxth"
_bool = "b"
_bytes = "sog"
_float = "d"
_var = "v"

_simple = Base(regex(f"[{_int}{_bool}{_bytes}{_float}{_var}]"))


@_simple.modifiers.append
def _(base, start, expr, end):
    if expr.result in _bytes:
        return bytes
    elif expr.result in _int:
        return int
    elif expr.result in _var:
        return Any
    elif expr.result in _float:
        return floar
    elif expr.result in _bool:
        return bool
    raise NotImplementedError(f"wtf! {expr}")


_tuple = MatchAll(
    [Ignore(Base(regex(r"\("))), MatchNtoM(_simple, n=1), Ignore(Base(regex(r"\)")))]
)

_single_expr = MatchFirst([_tuple, _simple])


@_tuple.modifiers.append
def _(base, start, expr, end):
    print(tuple(expr.result[0]))
    return Tuple.__getitem__(tuple(expr.result[0]))


_array = Wrap(None)
_array.wrapped = MatchAll(
    [Ignore(Base(regex("a"))), MatchFirst([_array, _single_expr])]
)


@_array.modifiers.append
def _(base, start, expr, end):
    return List[expr.result[0]]


_all = MatchFirst([_array, _single_expr])


@pytest.mark.parametrize(
    "expr,res",
    [("(sbsv)", Tuple[bytes, bool, bytes, Any]), ("v", Any), ("as", List[bytes])],
)
def test_dbus(expr, res):
    assert _all.parse(expr).result == res
