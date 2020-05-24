from ure import Base, MatchAll, Optional, Result


def test():
    op = Optional(Base("word"))
    assert op.parse("word") == Result("word", start=0, end=len("word"))
    assert op.parse("noword", match_all=False) == None


def test_composite():
    op = Optional(Base("no"))
    word = Base("word")
    no_word = MatchAll([op, word])
    assert no_word.parse("noword") == Result(["no", "word"], start=0, end=len("noword"))
    assert no_word.parse("word") == Result(["word"], start=0, end=len("word"))
