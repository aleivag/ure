import libcst as cst
from ure import Base, MatchAll, MatchFirst, MatchNtoM, Optional, Ignore
from dataclasses import fields

MOD = cst.parse_module("""

python_binary(
    name="your_name",
)
""")


def clean(node):
    yield node


def get_node_attr(name):
    def iterator(comp):
        for node in comp:
            if hasattr(node, name):
                yield getattr(node, name)

    return iterator


def get_node_idx(idx):
    idx = int(idx)

    def iterator(comp):
        for node in comp:
            if isinstance(node, tuple) and len(node) > idx:
                yield node[idx]

    return iterator


def children(comp):
    for node in comp:
        if isinstance(node, tuple):
            yield from node
        elif isinstance(node, cst.CSTNode):
            for field in fields(node):
                yield getattr(node, field.name)


def rchildren(comp):
    def _r(node):
        yield node
        if isinstance(node, tuple):
            for n in node:
                yield from _r(n)
        elif isinstance(node, cst.CSTNode):
            for field in fields(node):
                yield from _r(getattr(node, field.name))
        else:
            yield node

    for node in comp:
        yield from _r(node)


def unimplemented(name):
    def __(text, start, result, end):
        def _(comp):
            raise NotImplementedError(f"fuck of!, {name} not implemented")

        return _

    return __


ROOT = Base(r"/", ws=None, modifiers=[lambda *a: clean])


IDX = Base(r"\d+", ws=None, modifiers=[lambda t, s, r, e: get_node_idx(r.result)])
ATTR = Base(r"\w+", ws=None, modifiers=[lambda t, s, r, e: get_node_attr(r.result)])
DEEPSTAR = Base(r"\*\*", ws=None, modifiers=[lambda t, s, r, e: rchildren])
STAR = Base(r"\*", ws=None, modifiers=[lambda t, s, r, e: children])


# not implemented yet!
PARENT = Base(r"\.\.", ws=None, modifiers=[lambda t, s, r, e: unimplemented("parent")])

### FIlter

# [ + expr + ]

FUNC = Base(r"(node_type|code)\(\)")


COMP = MatchAll([])

FILTER = MatchAll(
    [
        Base(r"\["),
        Base(r"\]"),
    ]
)

###


SEP = Base(r"/", ws=None)

QPART = MatchFirst([DEEPSTAR, STAR, IDX, ATTR])

PART = MatchAll([QPART, Ignore(SEP)], modifiers=[lambda t, s, r, e: r.result[0]])
PARTS = MatchNtoM(PART)

QUERY = MatchAll([ROOT, PARTS, Optional(QPART)])


@QUERY.modifiers.append
def _(text, start, result, end):
    root, parts, tail = (
        result.result if len(result.result) == 3 else (*result.result, None)
    )
    compose = root(MOD)
    for part in parts:
        compose = part(compose)

    if tail:
        compose = tail(compose)

    return compose


def test_root():
    assert list(QUERY.parse("/").result) == [MOD]


def test_body():
    assert list(QUERY.parse("/body").result) == [MOD.body]


def test_body_trailing():
    assert list(QUERY.parse("/body/").result) == [MOD.body]


def test_noattr():
    assert list(QUERY.parse("/no_body").result) == []


def test_body_0_body():
    assert list(QUERY.parse("/body/0/body").result) == [MOD.body[0].body]


def test_body_STAR_body():
    assert list(QUERY.parse("/body/*/body").result) == [MOD.body[0].body]


def test_STAR_STAR_body():
    assert list(QUERY.parse("/*/*/body").result) == [MOD.body[0].body]


def test_DEEP_STAR_body():
    assert list(QUERY.parse("/**/0/body").result) == [MOD.body[0].body]


def test_all_body():
    assert list(QUERY.parse("/**/body").result) == [MOD.body, MOD.body[0].body]


def test_get_func_call():
    assert list(QUERY.parse("/**/func/value").result) == ["python_binary"]


# def test_parent():
#     assert list(QUERY.parse("/**/func/value/..").result) == ["python_binary"]
