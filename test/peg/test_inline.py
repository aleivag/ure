import ure.peg


def test_inline():
    parser = ure.peg.Parser()
    assert parser.inline("line", "/\w+/").parse("hello").result == "hello"
