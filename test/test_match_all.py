import pytest
from ure import MatchAll, Base, regex, Result


def test_match_first_basic():
    val = "____ 12345 alvaro"
    result = Result(val.split(" "), start=0, end=len(val))
    assert MatchAll([Base("_+"), Base(r"\d+"), Base(r"\w+")]).parse(val) == result


def test_match_first_basic_non_result():
    val = "____ 12345 alvaro"
    num = Base(r"\d+", modifiers=[lambda b, s, result, end: (int(result.result), end)])
    under, anum, aname = val.split(" ")

    result = Result([under, int(anum), aname], start=0, end=len(val))
    assert MatchAll([Base("_+"), num, Base(r"\w+")]).parse(val) == result
