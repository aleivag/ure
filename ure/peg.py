import functools
import re
from typing import Any, Tuple

from ure import (
    Base,
    Ignore,
    MatchAll,
    MatchFirst,
    MatchNtoM,
    Optional,
    Result,
    Wrap,
    regex,
    by_result,
)
from ure.extra import Integer, Number, IPv4, IPv6, IP, delimited_list

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

    return Result(Base(reg))


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

    def _namefy(self, base, start, result, end) -> Tuple[Result, int]:
        if result:
            result.names[self.name] = result.result
        return result

    def __repr__(self) -> str:
        return f"@{self.name}:{self.wrapped}"


class ParseAction(object):
    def __init__(self, name: str, parser, fnc) -> None:
        self.parser = parser
        self.name = name
        self.fnc = fnc

    @property
    def expr(self):
        return self.parser.compile(self.name)

    def parse(self, string: str, match_all: bool = True):
        expr = self.expr
        return expr.parse(string, match_all=match_all)

    def inner_parse(self, base: str, start: int = 0):
        expr = self.expr
        return expr.inner_parse(base, start)


class Parser:
    OPEN_PARENTHESIS = Base(r"\(")
    CLOSE_PARENTHESIS = Base(r"\)")

    OPERATOR_AND = Base(r"\&")
    OPERATOR_OR = Base(r"\|")
    OPERATOR_NAME = Base(":")

    NAME = Base(r"@[a-zA-Z_]\w+")
    FUNC = Base(r"\$[a-zA-Z_]\w+")

    def __init__(self) -> None:
        self.expr = {
            "integer": Integer,
            "number": Number,
            "ipv4": IPv4,
            "ipv6": IPv6,
            "ip_address": IP,
        }
        self.tokens = {}
        self.funcs = {"delimited_list": delimited_list}

        # lets define the parser
        self.literal = Base(
            r"([\"\'/])(?P<content>.*?(?<!\\)(\\\\)*)\1(?P<mods>[ilmsux]*)",
            modifiers=[self.get_literal],
        )

    def get_or(self, base: str, start: int, result: Any, end: int) -> Tuple[Any, int]:
        return MatchFirst

    def get_and(self, base: str, start: int, result: Any, end: int) -> Tuple[Any, int]:
        return MatchAll

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

        return Base(reg)

    def _namefy(
        self, base: str, start: int, result: Result, end: int
    ) -> Tuple[Any, int]:
        return Namefy(result.result[0][1:], result.result[2])

    def _funcify(self, result: Result):
        func_name = result.result[0][1:]
        args = result.result[2] if isinstance(result.result[2], list) else []
        return self.funcs[func_name](*args)

    def _inner_algebra(
        self, base: str, start: int, result: Result, end: int
    ) -> Tuple[Any, int]:
        a, o, b = result.result

        return o([a, b])

    def _parentesis(
        self, base: str, start: int, result: Result, end: int
    ) -> Tuple[Any, int]:
        return result.result[1]

    @property
    @functools.lru_cache()
    def pegparser(self) -> Base:
        # lets grow this
        parser = Wrap(None)
        algebra = Wrap(None)
        namefy = Wrap(None)
        funcify = Wrap(None)

        op_or = Base(r"\|", modifiers=[self.get_or])
        op_and = Base(r"\&", modifiers=[self.get_and])

        right_on = Base(r"[\*\+\!\?]*")

        infix_operand = MatchFirst([op_or, op_and])

        literal = Base(
            r"([\"\'/])(?P<content>.*?(?<!\\)(\\\\)*)\1(?P<mods>[ilmsux]*)",
            modifiers=[self.get_literal],
        )

        token = Base(r"\w+", modifiers=[lambda b, s, r, e: self.compile(r.result)])

        tokey = MatchFirst([funcify, literal, token])

        func_arg_list = Optional(delimited_list(tokey, Base(",")))
        funcify.wrapped = MatchAll(
            [self.FUNC, Base(r"\["), func_arg_list, Base(r"]")],
            modifiers=[by_result(self._funcify)],
        )

        global_expr = MatchAll(
            [self.OPEN_PARENTHESIS, algebra, self.CLOSE_PARENTHESIS],
            modifiers=[self._parentesis],
        )

        primary = MatchAll([MatchFirst([tokey, global_expr]), right_on])

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

            return r

        inner_name = MatchAll(
            [self.NAME, self.OPERATOR_NAME, primary], modifiers=[self._namefy]
        )

        namefy.wrapped = MatchFirst([inner_name, primary])

        inner_algebra = MatchAll(
            [namefy, infix_operand, algebra], modifiers=[self._inner_algebra]
        )

        algebra.wrapped = MatchFirst([inner_algebra, namefy])

        return algebra

    def compile(self, token: str) -> Base:
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

        if isinstance(k, Base):
            # someone give us a expression already, lets return that
            self.tokens[token] = k
            return self.tokens[token]

        self.tokens[token] = FutureToken()
        parsed_expr = self.pegparser.parse(k.strip()).result

        if v:
            parsed_expr.modifiers.append(v)

        if isinstance(self.tokens[token], FutureToken):
            self.tokens[token] = parsed_expr

        else:
            self.tokens[token].wrapped = parsed_expr

        return self.tokens[token]

    def peg(self, peg_expr, name=None, decorator=None):
        def binder(fnc):
            _name = name if name else fnc.__name__
            if decorator:
                fnc = decorator(fnc)

            self.expr.update({_name: (peg_expr, fnc)})

            return ParseAction(_name, self, fnc)

        return binder

    def func(self, name=None):
        def binder(fnc):
            _name = name if name else fnc.__name__
            self.funcs.update({_name: fnc})
            return fnc

        return binder

    def inline(self, name, peg_expr, fnc=None):
        assert name not in self.expr, f"name {name} already exists"
        self.expr[name] = (peg_expr, fnc)
        return ParseAction(name, self, fnc)
