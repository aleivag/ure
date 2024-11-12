from datetime import datetime, timedelta

import pytest

from ure import by_name, by_result
from ure.peg import Parser

parser = Parser()

DELTAS = {
    "w": timedelta(days=7),
    "d": timedelta(days=1),
    "h": timedelta(seconds=60 * 60),
    "m": timedelta(seconds=60),
    "s": timedelta(seconds=1),
}

OP = {"+": lambda x, y: x + y, "-": lambda x, y: x - y}

parser.expr.update(
    {
        "time_unit": ("/[wdhms]/", by_result(lambda r: DELTAS[r.result])),
        "delta_time": (
            "@value:integer & @unit:time_unit",
            by_name(lambda value, unit: value * unit),
        ),
    }
)


@parser.peg(" 'now|tomorrow|yesterday' ", decorator=by_result)
def base_time(result):
    now = datetime.now()

    if result.result == "now":
        return timedelta(seconds=0)
    elif result.result == "tomorrow":
        return DELTAS["d"]
    elif result.result == "yesterday":
        return -DELTAS["d"]
    return now + delta


@parser.peg("@left:base_time & @deltas:(/[+-]/ & delta_time)*", decorator=by_name)
def time_expr(left, deltas):
    for op, right in deltas:
        left = OP[op](left, right)
    return left


@pytest.mark.parametrize("expr, res", DELTAS.items())
def test_time_unit(expr, res):
    parser.compile("time_unit").parse(expr).result == res


@pytest.mark.parametrize("expr, res", DELTAS.items())
def test_delta_time(expr, res):
    parser.compile("delta_time").parse(f" 1 {expr}").result == res


@pytest.mark.parametrize("bt", ["now", "tomorrow", "yesterday"])
def test_base_time(bt):
    base_time.parse(bt)


@pytest.mark.parametrize(
    "expr,res",
    [
        ("now", timedelta(seconds=0)),
        ("now + 7w", timedelta(seconds=0) + 7 * timedelta(days=7)),
        (
            "now + 7w - 2h",
            timedelta(seconds=0) + 7 * timedelta(days=7) - 2 * timedelta(hours=1),
        ),
    ],
)
def test_td(expr, res):
    assert time_expr.parse(expr).result == res
