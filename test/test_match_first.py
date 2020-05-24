import pytest

from ure import Base, MatchFirst, Result, regex


@pytest.mark.parametrize("val", ["____", "12345", "alvaro"])
def test_match_first_basic(val):
    assert MatchFirst(
        [Base(regex("_+")), Base(regex(r"\d+")), Base(regex(r"\w+"))]
    ).parse(val) == Result(val, start=0, end=len(val))
