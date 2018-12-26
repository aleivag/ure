import pytest
from epiparsing.extra import Integer


@pytest.mark.parametrize("num", [0, 10, 43, -1, -42])
def test_integer(num):
    assert Integer.parse(f"{num}").result == num
