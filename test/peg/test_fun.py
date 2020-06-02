from ure import by_name
from ure.peg import Parser


parser = Parser()
parser.expr.update(
    {
        "hello": r"$hello_world[]",
        "clean_hello": r"$no_ws[ /hello/ ]",
        "clean_hello_world": r"$no_ws[ $hello_world[] ]",
        "delim": r"$int_csv[/\d+/, /,/]",
        "named_delim": r"@name:$int_csv[/\d+/, /,/]",
    }
)


@parser.func()
def hello_world():
    return Parser().inline("inline", "'Hello'i & 'World'i")


@parser.func()
def no_ws(expr):
    expr.ws = None
    return expr


@parser.func()
def int_csv(expr, sep):
    p = Parser()
    # breakpoint()

    p.expr.update({"expr": expr, "sep": sep})

    @p.peg("sep! & expr")
    def tail(text, start, result, end):
        return result.result[0]

    @p.peg("@head:expr & @tail:tail*?  & sep?!", name="rm")
    @by_name()
    def _(head, tail):
        return [head, *tail]

    return p.compile("rm")


def test_no_arg_func():
    assert parser.compile("hello").parse("hello world").result == ["hello", "world"]


def test_single_arg():
    assert parser.compile("clean_hello").parse("hello").result == "hello"


def test_single_arg_is_func():
    assert parser.compile("clean_hello_world").parse("hello world").result == [
        "hello",
        "world",
    ]


def test_doble_args():
    assert parser.compile("delim").parse("42, 42, 42").result == ["42", "42", "42"]


def test_named_func():
    assert parser.compile("named_delim").parse("42, 42, 42").names["name"] == [
        "42",
        "42",
        "42",
    ]
