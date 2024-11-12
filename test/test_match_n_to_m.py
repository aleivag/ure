import pytest

from ure import Base, MatchNtoM, Result, ResultNotFoundError, regex

LONG_TEXT = "long text that should match all"
LENTH_LONG_TEXT = len(LONG_TEXT.split())


@pytest.mark.parametrize("n", [0, 1, LENTH_LONG_TEXT])
def test_match_only_n(n: int):
    assert MatchNtoM(Base(regex(r"\w+")), n).parse(LONG_TEXT) == Result(
        LONG_TEXT.split(), start=0, end=len(LONG_TEXT)
    )


@pytest.mark.parametrize("n", [LENTH_LONG_TEXT + 1, LENTH_LONG_TEXT + 100])
def test_no_match_n_is_large(n):
    with pytest.raises(ResultNotFoundError):
        MatchNtoM(Base(regex(r"\w+")), n).parse(LONG_TEXT)


@pytest.mark.parametrize("m", [LENTH_LONG_TEXT, LENTH_LONG_TEXT + 100])
def test_match_only_m(m: int):
    assert MatchNtoM(Base(regex(r"\w+")), 0, m).parse(LONG_TEXT) == Result(
        LONG_TEXT.split(), start=0, end=len(LONG_TEXT)
    )


@pytest.mark.parametrize("m", [0, 1, LENTH_LONG_TEXT - 1])
def test_no_match_m_is_small(m):
    with pytest.raises(ResultNotFoundError):
        MatchNtoM(Base(regex(r"\w+")), 0, m).parse(LONG_TEXT)
