from ure import Base, MatchAll, MatchNtoM, ResultNotFoundError, Wrap, regex, by_result

### some extra modifiers


def nullify(base, start, result, end):
    return None


@by_result()
def cast_to_int(result):
    return int(result.result)


@by_result()
def cast_to_float(result):
    return float(result.result)


Integer = Base(regex(r"[\+-]?\d+"), modifiers=[cast_to_int])
Number = Base(regex(r"[-+]?([0-9]*\.[0-9]+|[0-9]+)"), modifiers=[cast_to_float])


class Between(Wrap):
    def _between(self, base, start, result, end):
        if self.lower <= result.result <= self.upper:
            return result
        raise ResultNotFoundError()

    def __init__(self, lower, upper):
        self.wrapped = Integer
        self.lower, self.upper = lower, upper
        self._modifiers = [self._between]


Name = Base(regex(r"[_\w][_\w\d]*"))
