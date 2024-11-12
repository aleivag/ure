import pytest

from ure import Result, ResultNotFoundError
from ure.extra import Between

OCTET = Between(0, 255)
MIN_ONE = Between(-1, 1)


@pytest.mark.parametrize("val", [0, 100, 200, 255])
def test_in_between(val):
    assert OCTET.parse(f"{val}") == Result(val, start=0, end=len(f"{val}"))


@pytest.mark.parametrize("val", [300, -42])
def test_not_in_between(val):
    with pytest.raises(ResultNotFoundError):
        OCTET.parse(f"{val}")


@pytest.mark.parametrize("val", [-1, 0, 1])
def test_in_between_one(assert_result, val):
    assert_result(MIN_ONE.parse(f"{val}"), Result(val))
