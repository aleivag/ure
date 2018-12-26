import pytest
from epiparsing import Result


@pytest.fixture
def assert_result():
    def _assert(resulta: Result, resultb: Result):
        assert resulta.result == resultb.result
        assert resulta.names == resultb.names

    return _assert
