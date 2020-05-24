import pytest

from ure import Result


def test_add(parser):
    parser.expr.update(
        {
            "str1": "'str1'",
            "str2": '"str2"',
            "regx": r"/\d+/",
            "comb": "str1 &  str2 &  regx",
        }
    )
    comb = parser.compile("comb")
    assert comb.parse("str1 str2 42") == Result(
        ["str1", ["str2", "42"]], start=0, end=len("str1 str2 42")
    )
    assert comb.parse("    str1     str2     42") == Result(
        ["str1", ["str2", "42"]], start=0, end=len("    str1     str2     42")
    )
    assert comb.parse("str1str242") == Result(
        ["str1", ["str2", "42"]], start=0, end=len("str1str242")
    )


# def test_or(parser):
#     parser.expr.update(
#         {
#             "str1": "'str1'",
#             "str2": '"str2"',
#             "regx": "/\d+/",
#             "comb": "str1 |  str2  | regx",
#         }
#     )
#     comb = parser.compile()["comb"]
#     assert comb.parseString("str1")[0] == "str1"
#     assert comb.parseString("str2")[0] == "str2"
#     assert comb.parseString("42")[0] == "42"


# def test_parentesis(parser, pyparsing):
#     parser.expr.update(
#         {
#             "str1": "'str1'",
#             "str2": '"str2"',
#             "regx": "/\d+/",
#             "combA": "(str1 |  str2)   regx",
#             "combB": "str1   (str2  | regx)",
#         }
#     )
#     c = parser.compile()

#     assert list(c["combA"].parseString("str1 42")) == ["str1", "42"]
#     assert list(c["combA"].parseString("str2 42")) == ["str2", "42"]

#     assert list(c["combB"].parseString("str1 42")) == ["str1", "42"]
#     assert list(c["combB"].parseString("str1 str2")) == ["str1", "str2"]

#     with pytest.raises(pyparsing.ParseException):
#         c["combA"].parseString("str1 str2 42")
#         c["combA"].parseString("str1 str2")

#         c["combB"].parseString("str1 str2 42")
#         c["combB"].parseString("str2 42")


# def test_suppression(parser):
#     parser.expr.update(
#         {"str1": "'str1'", "str2": '"str2"', "regx": "/\d+/", "comb": " str1!  regx"}
#     )

#     c = parser.compile()
#     assert c["comb"].parseString("str1 42")[0] == "42"


def test_naming(parser):
    parser.expr.update(
        {
            "str1": "'str1'",
            "str2": '"str2"',
            "regx": r"/\d+/",
            "comb": "@head:str1 & @tail:regx",  #  @tail:regx",
            "ocomb": "@head:str1 | @tail:regx",
        }
    )

    comb = parser.compile("comb")
    ocomb = parser.compile("ocomb")
    assert comb.parse("str1 42").names == {"head": "str1", "tail": "42"}
    assert ocomb.parse("42").names == {"tail": "42"}
    assert ocomb.parse("str1").names == {"head": "str1"}
