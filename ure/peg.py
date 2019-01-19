import re
from typing import Any, Tuple
from ure import (
    Base,
    Wrap,
    regex,
    Result,
    MatchNtoM,
    MatchFirst,
    MatchAll,
    Optional,
    Ignore,
)
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


class FutureToken:
    pass


def reduce_infix(base, extra):
    e = extra[0]
    acum = [e[0], [base, e[1]]]
    for operator, operand in extra[1:]:
        if operator == acum[0]:
            acum[1].append(operand)
        else:
            acum = [operator, [acum[0](acum[1]), operand]]

    return acum[0](acum[1])


class Namefy(Wrap):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.modifiers.append(self._namefy)

    def _namefy(self, base, start, result, end):
        result.names[self.name] = result.result
        return result, end

    def __repr__(self):
        return f"@{self.name}:{self.wrapped}"


class Parser:
    OPEN_PARENTHESIS = Base(r"\(")
    CLOSE_PARENTHESIS = Base(r"\)")

    OPERATOR_AND = Base(r"\&")
    OPERATOR_OR = Base(r"\|")
    OPERATOR_NAME = Base(":")

    NAME = Base("@[a-zA-Z_]\w+")

    def __init__(self):
        self.expr = {}
        self.tokens = {}

        # lets define the parser
        self.literal = Base(
            r"([\"\'/])(?P<content>.*?(?<!\\)(\\\\)*)\1(?P<mods>[ilmsux]*)",
            modifiers=[self.get_literal],
        )

    def get_or(self, base: str, start: int, result: Any, end: int) -> Tuple[Any, int]:
        return MatchFirst, end

    def get_and(self, base: str, start: int, result: Any, end: int) -> Tuple[Any, int]:
        return MatchAll, end

    def get_literal(
        self, base: str, start: int, result: Any, end: int
    ) -> Tuple[Any, int]:
        mods = result.names["mods"].upper()
        reg = regex(
            result.names["content"],
            flags=functools.reduce(
                lambda acum, val: acum | getattr(re, val),
                mods[1:],
                getattr(re, mods[0]),
            )
            if result.names["mods"]
            else 0,
        )

        return Base(reg), end

    @property
    def pegparser(self):
        # lets grow this
        parser = Wrap(None)

        # ob = Base(r"\(")
        # cb = Base(r"\)")

        op_or = Base(r"\|", modifiers=[lambda b, s, r, e: (MatchFirst, e)])
        op_and = Base(r"\&", modifiers=[lambda b, s, r, e: (MatchAll, e)])

        right_on = Base(
            r"[\*\+\!\?]*",
            # modifiers=[lambda b, s, result, end: (result if result.result else None, end)],
        )

        name_symbol = Base(":")

        infix_operand = MatchFirst([op_or, op_and])

        literal = Base(
            r"([\"\'/])(?P<content>.*?(?<!\\)(\\\\)*)\1(?P<mods>[ilmsux]*)",
            modifiers=[self.get_literal],
        )

        name_identifier = Base(r"@\w+")

        algebra = Wrap(None)
        namefy = Wrap(None)

        global_expr = MatchAll([self.OPEN_PARENTHESIS, algebra, self.CLOSE_PARENTHESIS])

        @global_expr.modifiers.append
        def parentesis(base, start, result, end):
            return result.result[1], end

        primary = MatchAll([MatchFirst([literal, global_expr]), right_on])

        @primary.modifiers.append
        def say_what(base, start, result, end):
            r = result
            r = result.result[0]
            for mod in result.result[1]:
                if mod == "*":
                    r = MatchNtoM(r, n=0)
                elif mod == "+":
                    r = MatchNtoM(r, n=1)
                elif mod == "?":
                    r = Optional(r)
                elif mod == "!":
                    r = Ignore(r)

            return r, end

        inner_name = MatchAll([name_identifier, name_symbol, primary])

        @inner_name.modifiers.append
        def inner_namefy(base, stat, result, end):
            return Namefy(result.result[0][1:], result.result[2]), end

        namefy.wrapped = MatchFirst([inner_name, primary])

        # @namefy.wrapped.modifiers.append
        # def _namefy(base, start, result, end):
        #     return result, end

        inner_algebra = MatchAll([namefy, infix_operand, algebra])

        @inner_algebra.modifiers.append
        def inner_algebra_mod(base, start, result, end):
            a, o, b = result.result

            return o([a, b]), end

        algebra.wrapped = MatchFirst([inner_algebra, namefy])

        return algebra

    def compile(self, token):
        tok = self.tokens.get(token)

        if isinstance(tok, FutureToken):
            # we are procesing this definition, and its a recursive one
            # return it.
            self.tokens[token] = Wrap(None)
            return self.tokens[token]

        if tok:
            # we know this, we have process it before, just return it.
            return tok

        # we dont know the token, lets get it from expr
        expr = self.expr[token]

        if isinstance(expr, (list, tuple)):
            k, v = expr
        else:
            k, v = expr, None

        # lets assume that k can only be a string for a moment

        parsed_expr = self.pegparser.parse(k.strip())

        return parsed_expr
