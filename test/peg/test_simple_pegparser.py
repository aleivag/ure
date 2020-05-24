import re

import pytest

from ure import Base, Ignore, MatchAll, MatchFirst, MatchNtoM, Optional, Result
from ure.peg import Namefy, Parser, reduce_infix


@pytest.fixture()
def simple_parser():
    return Parser()


@pytest.mark.parametrize("token", "'\"/")
@pytest.mark.parametrize("ob,cp", [("(", ")"), ("", "")])
@pytest.mark.parametrize("modi,re_modi", [("", 0), ("i", re.I)])
def test_literal(simple_parser, token, ob, cp, modi, re_modi):
    expr = f"{ob}{token}ure{token}{modi}{cp}"
    lit = simple_parser.pegparser.parse(expr).result
    assert isinstance(lit, Base)
    assert lit.expr == re.compile("ure", re_modi)
    assert lit.parse("ure") == Result("ure", start=0, end=3)


@pytest.mark.parametrize("operator", "&|")
@pytest.mark.parametrize("token", "'\"/")
@pytest.mark.parametrize("ob,cp", [("(", ")"), ("", "")])
@pytest.mark.parametrize("nwords", [2, 3, 4])
def test_infix(simple_parser, operator, token, ob, cp, nwords):
    base_word = "word"
    words = [f"{ob}  {token}{base_word}{n}{token}   {cp}" for n in range(nwords)]
    expr = operator.join(words)
    lit = simple_parser.pegparser.parse(expr).result

    e = lit.exprs[:]
    for _ in range(nwords - 2):
        last = e[-1]
        e[-1] = last.exprs[0]
        e.append(last.exprs[-1])

    assert [i.expr for i in e] == [Base(f"{base_word}{n}").expr for n in range(nwords)]


@pytest.mark.parametrize(
    "right, rightbase",
    [("?", Optional), ("!", Ignore), ("*", MatchNtoM), ("+", MatchNtoM)],
)
@pytest.mark.parametrize("ws", [" ", ""])
@pytest.mark.parametrize("op,cp", [("(", ")"), ("", "")])
def test_right(simple_parser, right, rightbase, ws, op, cp):
    expr = f" {op}'hey'{ws}{cp}{ws}{right} ".strip()
    lit = simple_parser.pegparser.parse(expr).result
    assert isinstance(lit, rightbase)


# special cases


@pytest.mark.parametrize("cases", ["@name: 'hey'", "@name: ('hey')", "(@name: 'hey')"])
def test_names(simple_parser, cases):
    lit = simple_parser.pegparser.parse(cases.strip()).result
    assert isinstance(lit, Namefy)
    assert lit.parse("hey").names["name"] == "hey"


@pytest.mark.parametrize(
    "cases", ["@name: 'hey'*", "@name: ('hey')*", "@name: 'hey'+", "@name: ('hey')+"]
)
def test_names_with_right(simple_parser, cases):
    lit = simple_parser.pegparser.parse(cases.strip()).result
    assert isinstance(lit, Namefy)
    assert lit.parse("hey") == Result(["hey"], names={"name": ["hey"]}, start=0, end=3)

    assert lit.parse("hey hey") == Result(
        ["hey"] * 2, names={"name": ["hey"] * 2}, start=0, end=7
    )


@pytest.mark.parametrize("expr", ["a", "bc", "de"])
def test_parenthesis(simple_parser, expr):
    e = simple_parser.pegparser.parse(
        " 'a' | ('b' & 'c') | ('d' & 'e') ".strip()
    ).result

    assert e.parse(expr) == Result(
        list(expr) if len(expr) > 1 else expr, start=0, end=len(expr)
    )


@pytest.mark.parametrize("expr", ["a", "a" * 4])
@pytest.mark.parametrize("rep", ["+", "*"])
def test_repeat(simple_parser, expr, rep):
    e = simple_parser.pegparser.parse(f"'a'{rep}").result
    assert e.parse(expr) == Result(list(expr), start=0, end=len(expr))


def test_name_repeat(simple_parser):
    e = simple_parser.pegparser.parse(f"@name:'a'*").result
    assert e.parse("aaaa") == Result(
        list("aaaa"), names={"name": list("aaaa")}, start=0, end=len("aaaa")
    )


@pytest.mark.parametrize("expr", ["a", "bc"])
def test_infix_combinations(simple_parser, expr):
    # TODO: Better define this
    e = simple_parser.pegparser.parse(f"'a' | 'b' & 'c'").result
    assert e.parse(expr) == Result(
        list(expr) if len(expr) > 1 else expr, start=0, end=len(expr)
    )


@pytest.mark.parametrize("expr", ["a", "abc", "abcbc"])
def test_infix_and_repetition(simple_parser, expr):
    # TODO: Better define this
    e = simple_parser.pegparser.parse(f" 'a' & @name:('b' & 'c')*").result
    rep = [list("bc") for _ in range(0, len(expr) - 1, 2)]
    r = ["a", rep]
    assert e.parse(expr) == Result(r, names={"name": rep}, start=0, end=len(expr))


def test_extra_cases(simple_parser):
    parser = simple_parser
    r = parser.pegparser.parse(" 'us' & ('(?P<me>you)' )   ".strip()).result.parse(
        "us you"
    )

    assert r == Result(["us", "you"], names={"me": "you"}, start=0, end=6)
