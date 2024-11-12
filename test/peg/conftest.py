import pytest

from ure.peg import Parser


@pytest.fixture
def parser():
    return Parser()
