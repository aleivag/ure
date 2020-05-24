from datetime import timedelta

import pytest

from ure import Base, by_name, by_result
from ure.peg import Parser

parser = Parser()


def flat(time_u):
    return (f"@num:integer & '{time_u}'", by_name(lambda num: num))


parser.expr.update(
    {"days": flat("d"), "hour": flat("h"), "min": flat("m"), "sec": flat("s")}
)


@parser.peg(
    """
    @days:days? &
    @hour:hour? &
    @min:min? &
    @sec:sec? 
""",
    decorator=by_result,
)
def timexpr(result):
    return timedelta(
        seconds=result.names.get("sec", 0),
        minutes=result.names.get("min", 0),
        hours=result.names.get("hour", 0),
        days=result.names.get("days", 0),
    )


@pytest.mark.parametrize(
    "texp,tdelta",
    [
        ("42d5m45s", timedelta(days=42, minutes=5, seconds=45)),
        ("42d5h45s", timedelta(days=42, hours=5, seconds=45)),
        ("70s", timedelta(seconds=70)),
    ],
)
def test_timexpr(texp, tdelta):
    assert timexpr.parse(texp).result == tdelta
