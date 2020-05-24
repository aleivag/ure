# Universal Regular Expressions (ure)


`ure` is a library that allows you to extend regular expressions, so they can parse
more complex expressions, the most common use is `ure.peg` that allow you to parse complex text
by writing pseudo-PEG expressions. 

![travis-status](https://api.travis-ci.org/aleivag/ure.svg?branch=master)

Example use:
------------

You need to turn something like `{ 3 => 9, 4 => {1 => 2 } }` to a python 
dictionary, it consist of comma-delimited key/value enclosed by brackets, where a 
key can be an integer and value can be either an integer or another hash structure.


```python
from ure.peg import Parser

parser = Parser()

parser.expr.update(
    {
        "key": r"/\d+/",
        "val": "hasht | key",
        "kv": ('key & "=>"! & val', lambda t, s, r, e: (r.result[0], r.result[1][0])),
    }
)


@parser.peg(" @head:kv & @middle:(','! & kv)*")
def kvs(test, start, result, end):
    head = result.names["head"]
    m = [f[0] for f in result.names["middle"]]
    return [head, *m]


@parser.peg(" '{'! & @kvs:kvs & '}'! ")
def hasht(test, start, result, end):
    return {k: v for k, v in result.names["kvs"]}

print(hasht.parse('{ 3 => 9, 42 => {1 => 2 } }').result)

```

This will output:

    {'3': '9', '42': {'1': '2'}}