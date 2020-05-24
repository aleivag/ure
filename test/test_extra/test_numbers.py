import pytest

from ure.extra import Integer, Number


@pytest.mark.parametrize("num", [0, 10, 43, -1, -42])
def test_integer(num):
    assert Integer.parse(f"{num}").result == num


@pytest.mark.parametrize("num", ["0.0", "1.0", "43.42", "3.14", "-4", ".5", "-.8"])
def test_real(num):
    assert Number.parse(num).result == float(num)
