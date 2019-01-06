import re
from ure import Base, Wrap, regex, Result
import functools

TOKEN = Base(r"[a-zA-z_][\w_]*")
LITERAL = Base(r"([\"\'/])(?P<content>.*?(?<!\\)(\\\\)*)\1(?P<mods>[ilmsux]*)")


@LITERAL.modifiers.append
def convert_to_base(base, start, result, end):
    mods = result.names["mods"].upper()
    reg = regex(
        result.names["content"],
        flags=functools.reduce(
            lambda acum, val: acum | getattr(re, val), mods[1:], getattr(re, mods[0])
        )
        if result.names["mods"]
        else 0,
    )

    return Result(Base(reg)), end


class Parser:
    def __init__(self):
        self.expr = {}
        self.tokens = {}

    def compile(self):
        self.tokens = {
            key: val if isinstance(val, Base) else Wrap(None)
            for key, val in self.expr.items()
        }
