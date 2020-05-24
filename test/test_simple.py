import pytest

from ure import Base, Result, ResultNotFoundError, regex

RSTRING = "WHAEVS"


def test_simple_cases():
    assert Base(regex(RSTRING)).parse(RSTRING) == Result(
        RSTRING, start=0, end=len(RSTRING)
    )


def test_fail_to_parse_cases():
    with pytest.raises(ResultNotFoundError):
        assert Base(regex(RSTRING)).parse(RSTRING + " pus EXTRA CONTENT").result


def test_partial_parse():
    assert (
        Base(regex(RSTRING))
        .parse(RSTRING + " pus EXTRA CONTENT", match_all=False)
        .result
        == RSTRING
    )


def test_no_explisit_regex():
    assert Base(regex(RSTRING)).expr == Base(RSTRING).expr
