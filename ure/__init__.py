import ast
import inspect
import re
from contextlib import suppress
from functools import wraps
from typing import Any, Callable, Dict, List
from typing import Optional as TOptional
from typing import Pattern, Tuple, Union

MEM_REGEX: Dict[int, Pattern] = {}


def regex(expr: str, flags: int = 0) -> Pattern:
    h = hash((expr, flags))
    if h not in MEM_REGEX:
        MEM_REGEX[h] = re.compile(expr, flags)

    return MEM_REGEX[h]


class ResultTuple:
    def __init__(self, result: Any, end: int):
        self.result = result
        self.end = end


class Result:
    def __init__(
        self,
        result: List[Any],
        names: Dict[str, Any] = None,
        start: int = None,
        end: int = None,
    ):
        self.result = result
        self.names = names or {}
        self.start, self.end = start, end

    def __repr__(self) -> str:
        return f"<Result {self.result} {self.names} [{self.start}, {self.end}) >"

    def __eq__(self, result_b):
        return (result_b.result, result_b.names, result_b.start, result_b.end) == (
            self.result,
            self.names,
            self.start,
            self.end,
        )


class ResultNotFoundError(Exception):
    pass


class Base:
    def __init__(
        self,
        expr: Union[str, Pattern],
        ws: Pattern = regex(r"\s*"),
        modifiers: TOptional[
            List[Callable[[str, int, Result, int], Tuple[Result, int]]]
        ] = None,
    ) -> None:
        self.expr = regex(expr) if isinstance(expr, str) else expr
        self._ws = ws
        self._modifiers = modifiers or []

    def __repr__(self) -> str:
        return f"/{self.expr}/"

    @property
    def ws(self) -> Pattern:
        self._ws = getattr(self, "_ws", regex(r"\s*"))
        return self._ws

    @ws.setter
    def ws(self, value) -> None:
        self._ws = value

    @property
    def modifiers(self) -> List[Callable[[str, int, Result, int], Tuple[Result, int]]]:
        self._modifiers = getattr(self, "_modifiers", [])
        return self._modifiers

    def parse(self, base: str, match_all: bool = True):
        result, end = self.inner_parse(base)
        if match_all and end != len(base):
            _, end = self.parse_ws(base, end)
            if end != len(base):
                raise ResultNotFoundError()
        return result

    def _parse_any(self, base: str, start: int, e: Pattern) -> Tuple[str, int]:
        """Match a single expr"""
        result = e.match(base, start)
        if result:
            return result, result.end()
        raise ResultNotFoundError()

    def parse_ws(self, base: str, start: int) -> Tuple[str, int]:
        ws = self.ws
        if ws:
            return None, self._parse_any(base, start, ws)[1]
        return None, start

    def parse_expr(self, base: str, start: int) -> Tuple[Result, int]:
        expr, end = self._parse_any(base, start, self.expr)
        return Result(expr.group(), names=expr.groupdict(), start=start, end=end), end

    def inner_parse(self, base: str, start: int = 0) -> Tuple[Result, int]:
        _, start = self.parse_ws(base, start)

        expr, end = self.parse_expr(base, start)
        for modifier in self.modifiers:
            mod = modifier(base, start, expr, end)
            if isinstance(mod, ResultTuple):
                result, end = mod.result, mod.end
            else:
                result = mod

            if not isinstance(result, (Result, type(None))):
                expr.result = result
            else:
                expr = result

        return expr, end


class Wrap(Base):
    def __init__(
        self,
        wrapped: Base,
        modifiers: TOptional[
            List[Callable[[str, int, Result, int], Tuple[Result, int]]]
        ] = None,
    ):
        self.wrapped = wrapped
        self._modifiers = modifiers or []

    def __repr__(self):
        return f"Wrap(...)"

    def inner_parse(self, base: str, start: int = 0) -> Tuple[Result, int]:
        expr, end = self.wrapped.inner_parse(base, start)
        for modifier in self.modifiers:
            mod = modifier(base, start, expr, end)
            if isinstance(mod, ResultTuple):
                result, end = mod.result, mod.end
            else:
                result = mod

            if not isinstance(result, (Result, type(None))):
                expr.result = result
            else:
                expr = result
        return expr, end


class Composed(Base):
    @property
    def ws(self):
        return None

    def parse_ws(self, base: str, start: int):
        return base, start


class MatchAll(Composed):
    def __init__(
        self,
        exprs: List[Base],
        modifiers: TOptional[
            List[Callable[[str, int, Result, int], Tuple[Result, int]]]
        ] = None,
    ) -> None:
        self.exprs = exprs
        self._modifiers = modifiers or []

    def __repr__(self):
        return " & ".join(f"{e}" for e in self.exprs)

    def parse_expr(self, base: str, start: int):
        result = Result([], start=start)
        for e in self.exprs:
            r, start = e.inner_parse(base, start)
            if isinstance(r, Result):
                result.result.append(r.result)
                result.names.update(r.names)
            elif r:
                result.result.append(r)

        result.end = start
        return result, start


class MatchFirst(Base):
    def __init__(
        self,
        exprs: List[Base],
        modifiers: TOptional[
            List[Callable[[str, int, Result, int], Tuple[Result, int]]]
        ] = None,
    ) -> None:
        self.exprs = exprs
        self._modifiers = modifiers or []

    def __repr__(self):
        return " | ".join(f"{e}" for e in self.exprs)

    def parse_expr(self, base: str, start: int):
        for e in self.exprs:
            with suppress(ResultNotFoundError):
                return e.inner_parse(base, start)
        raise ResultNotFoundError()


class MatchNtoM(Base):
    def __init__(
        self,
        expr: Base,
        n: int = 0,
        m=None,
        modifiers: TOptional[
            List[Callable[[str, int, Result, int], Tuple[Result, int]]]
        ] = None,
    ) -> None:
        self.expr = expr
        self.n = n
        self.m = m
        self._modifiers = modifiers or []

    def parse_expr(self, base: str, start: int):
        result = Result([], start=start)
        for _ in range(self.n):
            r, start = self.expr.inner_parse(base, start)

            result.result.append(r.result)

        i = self.n
        while i < (i + 1 if self.m is None else self.m):
            try:
                r, start = self.expr.inner_parse(base, start)
            except ResultNotFoundError:
                break
            result.result.append(r.result)
            i += 1
        result.end = start
        return result, start


class Ignore(Wrap):
    def __init__(self, wrapped):
        super().__init__(wrapped)
        self.modifiers.append(lambda base, start, result, end: None)


class Optional(MatchNtoM):
    def __init__(self, wrapped: Base, empty_on_no_result: bool = False):
        super().__init__(wrapped, 0, 1)
        if not empty_on_no_result:
            self.modifiers.append(self.optionalify)

    def optionalify(self, base, start, result, end):
        if result.result:
            result.result = result.result[0]
        else:
            result = None

        return result


def by_result(fnc=None):
    if not fnc:
        return by_result

    @wraps(fnc)
    def _(text, start, result, end):
        return fnc(result)

    return _


def by_name(fnc=None):
    if not fnc:
        return by_name

    expr_sig = inspect.signature(fnc).parameters

    @wraps(fnc)
    def _(text, start, result, end):
        return fnc(**{k: result.names[k] for k in expr_sig if k in result.names})

    return _


def extract_name(name):
    def _(text, start, result, end):
        return result.names[name]

    return _
