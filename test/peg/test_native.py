import pytest
from ure import Result, ResultNotFoundError, Base
import re
from ure.peg import TOKEN, LITERAL


@pytest.mark.parametrize("t", ("name", "_name", "n4m3", "n4_m43_"))
def test_passing_tokens(t):
    assert TOKEN.parse(t) == Result(t, start=0, end=len(t))


@pytest.mark.parametrize("t", ("3name", "@name", "n@me", "nam.me"))
def test_failing_tokens(t):
    with pytest.raises(ResultNotFoundError):
        TOKEN.parse(t) == Result(t)


def test_literal():
    p = LITERAL.parse("/hello/im")
    assert isinstance(p.result, Base)
    assert p.result.expr == re.compile("hello", re.I | re.M)
