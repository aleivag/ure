import re

from contextlib import suppress

from typing import Pattern, Dict, Tuple, List, Any, Optional, Callable, Union


MEM_REGEX: Dict[int, Pattern] = {}


def regex(expr: str, flags: int = 0) -> Pattern:
    h = hash((expr, flags))
    if h not in MEM_REGEX:
        MEM_REGEX[h] = re.compile(expr, flags)

    return MEM_REGEX[h]


class Result:
    def __init__(self, result: List[Any], names: Dict[str, Any] = None):
        self.result = result
        self.names = names or {}

    def __repr__(self) -> str:
        return f"<Result {self.result} {self.names}>"

    def __eq__(self, result_b):
        return (result_b.result, self.names) == (self.result, result_b.names)


class ResultNotFoundError(Exception):
    pass


class Base:
    def __init__(
        self,
        expr: Union[str, Pattern],
        ws: Pattern = regex(r"\s*"),
        modifiers: Optional[
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
            return result.group(), result.end()
        raise ResultNotFoundError()

    def parse_ws(self, base: str, start: int) -> Tuple[str, int]:
        return self._parse_any(base, start, self.ws)

    def parse_expr(self, base: str, start: int) -> Tuple[Result, int]:
        expr, end = self._parse_any(base, start, self.expr)
        return Result(expr), end

    def inner_parse(self, base: str, start: int = 0) -> Tuple[Result, int]:
        _, start = self.parse_ws(base, start)

        expr, end = self.parse_expr(base, start)
        for modifier in self.modifiers:
            expr, end = modifier(base, start, expr, end)
        return expr, end


class Wrap(Base):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def inner_parse(self, base: str, start: int = 0) -> Tuple[Result, int]:
        expr, end = self.wrapped.inner_parse(base, start)
        for modifier in self.modifiers:
            expr, end = modifier(base, start, expr, end)
        return expr, end


class Composed(Base):
    @property
    def ws(self):
        return None

    def parse_ws(self, base: str, start: int):
        return base, start


class MatchAll(Composed):
    def __init__(self, exprs: List[Base]) -> None:
        self.exprs = exprs

    def parse_expr(self, base: str, start: int):
        result = Result([])
        for e in self.exprs:
            r, start = e.inner_parse(base, start)
            if r:
                result.result.append(r.result)
        return result, start


class MatchFirst(Base):
    def __init__(self, exprs: List[Base]) -> None:
        self.exprs = exprs

    def parse_expr(self, base: str, start: int):
        for e in self.exprs:
            with suppress(ResultNotFoundError):
                return e.inner_parse(base, start)
        raise ResultNotFoundError()


class MatchNtoM(Base):
    def __init__(self, expr: Base, n: int = 0, m=None) -> None:
        self.expr = expr
        self.n = n
        self.m = m

    def parse_expr(self, base: str, start: int):
        result = Result([])
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
        return result, start


class Ignore(Wrap):
    def __init__(self, wrapped):
        super().__init__(wrapped)
        self.modifiers.append(lambda base, start, result, end: (None, end))


class Optional(MatchNtoM):
    def __init__(self, wrapped: Base, empty_on_no_result: bool = False):
        super().__init__(wrapped, 0, 1)
        if not empty_on_no_result:
            self.modifiers.append(
                lambda base, start, result, end: (
                    result if result.result else None,
                    end,
                )
            )
