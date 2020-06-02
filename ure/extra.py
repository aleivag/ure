from ure import (
    Base,
    MatchAll,
    MatchFirst,
    MatchNtoM,
    ResultNotFoundError,
    Wrap,
    regex,
    by_result,
    Result,
)

from ipaddress import IPv4Address, IPv6Address, AddressValueError

from contextlib import suppress

### some extra modifiers


def nullify(base, start, result, end):
    return None


Integer = Base(
    regex(r"[\+-]?\d+"), modifiers=[by_result(lambda result: int(result.result))]
)
Number = Base(
    regex(r"[-+]?([0-9]*\.[0-9]+|[0-9]+)([eE]\d+)?"),
    modifiers=[
        by_result(
            # life would be so much bettter if we could use `eval`
            lambda result: (
                float if any(t in result.result.lower() for t in (".", "e")) else int
            )(result.result)
        )
    ],
)


class Between(Wrap):
    def _between(self, base, start, result, end):
        if self.lower <= result.result <= self.upper:
            return result
        raise ResultNotFoundError()

    def __init__(self, lower, upper):
        self.wrapped = Integer
        self.lower, self.upper = lower, upper
        self._modifiers = [self._between]


# network

IPv4 = Base(
    r"(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})(\.(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3}",
    modifiers=[by_result(lambda r: IPv4Address(r.result))],
)

IPv6 = Base(
    r"([0-9a-fA-F]{1,4}:){6}(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})(\.(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3}|"
    r"(([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){0,4})?::([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){0,4})?)((25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})(\.(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3})|"
    "([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){7})|"
    "([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){0,6})?::([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){0,6})?"
)


@IPv6.modifiers.append
@by_result()
def _(result: Result) -> IPv6Address:
    print(result)  # * 1 / 0
    with suppress([ValueError, AddressValueError]):
        return IPv6Address(result.result)
    raise ResultNotFoundError(f"{result.result} is not an ipv6")


def delimited_list(expr, sep, trailing=True):
    tail_element = MatchAll([sep, expr], modifiers=[by_result(lambda r: r.result[1])])
    tail = MatchNtoM(tail_element)

    delim_list_parser = MatchAll(
        [expr, tail] + ([MatchNtoM(sep, n=0, m=1)] if trailing else []),
        modifiers=[by_result(lambda r: [r.result[0], *r.result[1]])],
    )

    return delim_list_parser


IP = MatchFirst([IPv6, IPv4])

Name = Base(regex(r"[_\w][_\w\d]*"))
