from ure import Base, Result
from ure.peg import Parser

SIMPLE_KEY = "simple"
COMPOUD_KEY = "compund"
HEY = "hey"
HO = "ho"


def test_simple_compile():
    parser = Parser()
    parser.expr.update({SIMPLE_KEY: "'hey' & 'ho'"})
    assert parser.compile(SIMPLE_KEY).parse("hey ho") == Result(
        ["hey", "ho"], start=0, end=6
    )


def test_simple_compund():
    parser = Parser()
    parser.expr.update({SIMPLE_KEY: "'hey' & 'ho'", COMPOUD_KEY: f"{SIMPLE_KEY}+"})

    assert parser.compile(COMPOUD_KEY).parse("hey ho") == Result(
        [["hey", "ho"]], start=0, end=6
    )


def test_simple2_compund():
    key = f"{HEY}_{HO}"
    val = f"'{HEY}' & '{HO}'"
    STR = f"{HEY} {HO}"
    parser = Parser()
    parser.expr.update({HEY: HEY, HO: HO, key: val})

    compiled = parser.compile(key)
    assert compiled.parse(STR) == Result([HEY, HO], start=0, end=len(STR))


def test_simple_peg_decorator():
    parser = Parser()

    @parser.peg("'hey'")
    def mult2(base, start, result, end):
        result.result = result.result * 2
        return result

    assert mult2.parse("hey") == Result("hey" * 2, start=0, end=3)


def test_accept_base():
    parser = Parser()
    NAME = "RANDOM_EXPR"
    parser.expr[NAME] = Base("hello")
    print(parser.compile(NAME))

    assert parser.compile(NAME).parse("hello") == Result(
        "hello", start=0, end=len("hello")
    )
