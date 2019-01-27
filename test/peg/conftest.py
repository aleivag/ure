from ure.peg import Parser

import pytest


@pytest.fixture
def parser():
    return Parser()
