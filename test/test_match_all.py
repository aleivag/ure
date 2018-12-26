import pytest
from epiparsing import MatchAll, Base, regex, Result


def test_match_first_basic():
    val = "____ 12345 alvaro"
    result = Result(val.split(" "))
    assert MatchAll([Base("_+"), Base(r"\d+"), Base(r"\w+")]).parse(val) == result
