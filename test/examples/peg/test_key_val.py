from ure import by_name
from ure.peg import Parser

parser = Parser()

parser.expr.update(
    {
        "key": r"/[\d\w]+/",
        "val": "hasht | key",
        "kv": ('key & "=>"! & val', lambda t, s, r, e: (r.result[0], r.result[1][0])),
        "kvs": "$delimited_list[kv, ',']",
    }
)


@parser.peg(" '{' & @kvs:kvs & '}' ", decorator=by_name)
def hasht(kvs):
    return dict(kvs)


def test_kv():
    assert hasht.parse("{ 3 => 9, 42 => {1 => 2 } }").result == {
        "3": "9",
        "42": {"1": "2"},
    }
