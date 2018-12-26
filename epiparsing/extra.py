from epiparsing import regex, Base, Wrap, ResultNotFoundError

### some extra modifiers


def nullify(base, start, result, end):
    return None, end


def cast_to_int(base, start, result, end):
    result.result = int(result.result)
    return result, end


Integer = Base(regex("[\+-]?\d+"), modifiers=[cast_to_int])


class Between(Wrap):
    def _between(self, base, start, result, end):
        if self.lower <= result.result <= self.upper:
            return result, end
        raise ResultNotFoundError()

    def __init__(self, lower, upper):
        self.wrapped = Integer
        self.lower, self.upper = lower, upper
        self._modifiers = [self._between]


Name = Base(regex(r"[_\w][_\w\d]*"))
