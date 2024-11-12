from ure.extra import delimited_list

from ure import Base, ResultNotFoundError

import pytest


def test_basic():
    assert delimited_list(Base(r"\w+"), Base(",")).parse("hello, world").result == [
        "hello",
        "world",
    ]

    assert delimited_list(Base(r"\w+"), Base(",")).parse(
        "goodbye, cruel, world"
    ).result == ["goodbye", "cruel", "world"]


def test_with_trailing():
    assert delimited_list(Base(r"\w+"), Base(","), trailing=True).parse(
        "hello, world,"
    ).result == ["hello", "world"]

    assert delimited_list(Base(r"\w+"), Base(","), trailing=True).parse(
        "hello, world"
    ).result == ["hello", "world"]

    assert delimited_list(Base(r"\w+"), Base(",")).parse("hello, world,").result == [
        "hello",
        "world",
    ], "trailing=True is not the default"


def test_with_no_trailing():
    assert delimited_list(Base(r"\w+"), Base(","), trailing=False).parse(
        "goodbye, cruel, world"
    ).result == ["goodbye", "cruel", "world"]

    with pytest.raises(ResultNotFoundError):
        delimited_list(Base(r"\w+"), Base(","), trailing=False).parse(
            "goodbye, cruel, world,"
        )
