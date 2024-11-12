import pytest

from ure import Result
from ure.peg import Parser


@pytest.fixture
def assert_result():
    def _assert(resulta: Result, resultb: Result):
        assert resulta.result == resultb.result
        assert resulta.names == resultb.names

    return _assert


@pytest.fixture
def parser():
    return Parser()
