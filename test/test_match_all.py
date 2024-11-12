import pytest

from ure import Base, MatchAll, Result, regex


def test_match_first_basic():
    val = "____ 12345 alvaro"
    test_result = Result(val.split(" "), start=0, end=len(val))
    real_result = MatchAll([Base("_+"), Base(r"\d+"), Base(r"\w+")]).parse(val)
    assert real_result == test_result


def test_match_first_basic_non_result():
    val = "____ 12345 alvaro"
    num = Base(r"\d+", modifiers=[lambda b, s, result, end: int(result.result)])
    under, anum, aname = val.split(" ")

    result = Result([under, int(anum), aname], start=0, end=len(val))
    assert MatchAll([Base("_+"), num, Base(r"\w+")]).parse(val) == result
