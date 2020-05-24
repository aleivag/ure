import pytest

from ure import Base, by_name
from ure.extra import Integer
from ure.peg import Parser

parser = Parser()


def sepval(expr, sep):
    parser = Parser()
    parser.expr.update({"expr": expr, "sep": sep})

    @parser.peg("sep! & expr")
    def tail(text, start, result, end):
        return result.result[0]

    @parser.peg("@head:expr & @tail:tail*?  & sep?!", name="rm")
    @by_name()
    def _(head, tail):
        return [head, *tail]

    return parser.compile("rm")


parser = sepval(Integer, Base(","))


@pytest.mark.parametrize(
    "expr,res",
    [
        ("1,2,3,4", [1, 2, 3, 4]),
        ("1,2,3,4,", [1, 2, 3, 4]),
        ("1 ,    2 ,   3\n,   4", [1, 2, 3, 4]),
    ],
)
def test_sepval(expr, res):
    assert parser.parse(expr, res).result == res


# print(
#     sepval(Base("\d+", modifiers=[lambda t, s, r, e: int(r.result)]), Base(",")).parse(
#         "1,2,3,4,"
#     )
# )
