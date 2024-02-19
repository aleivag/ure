# Universal Regular Expressions (ure)


`ure` is a library that allows you to extend regular expressions, so they can parse
more complex expressions, the most common use is `ure.peg` that allow you to parse complex text
by writing pseudo-PEG expressions.

Example use:
------------

You need to turn something like `{ 3 => 9, 4 => {1 => 2 } }` to a python 
dictionary, it consist of comma-delimited key/value enclosed by brackets, where a 
key can be an integer and value can be either an integer or another hash structure.


```python
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


print(hasht.parse("{ 3 => 9, 42 => {1 => 2 } }").result)
```

This will output:

    {'3': '9', '42': {'1': '2'}}


note: this is exampled in [this test](test/examples/peg/test_key_val.py)

Operations:
-----------

* **And** (*`&`*): If 2 tokens are separated by an *ampersand* (`&`) then 
they both need to match. for instance: 

```python
from ure.peg import Parser

parser = Parser()
parser.expr["greet"] = ' "hello" & "world" '

greet = parser.compile("greet")

greet.parse("hello world")  # returns ~ ["hello", "world"]

# Will fail and throw exception

greet.parse("hello cruel world")  # have a extra word
greet.parse("hello")  # missing "world"
```

The *and* operator return an array with 2 element, the left element, and the right element. Multiple 
*ampersand* are evaluated left to right, so:


```python
from ure.peg import Parser

parser = Parser()
parser.expr.update(
    {
        "greet1": ' "hello" & "cruel" & "world" ',
        "greet2": ' "hello" & ("cruel" & "world") ',
    }
)
# greet1 and greet2 return the same parser, that means that

result1 = parser.compile("greet1").parse("hello cruel world")
result2 = parser.compile("greet2").parse("hello cruel world")

result1.result == result2.result == ["hello", ["cruel", "world"]]
```


* **Or** (*`|`*): If 2 tokens are separated by a *pipe* (`|`) any one of them can match.
So `Hello ("world" | "you") ` will match "hello world" or "hello you".

```python
from ure.peg import Parser

parser = Parser()
parser.expr["greet"] = ' ("hello" | "goodbye") & "world" '

greet = parser.compile("greet")

greet.parse("hello world")  # returns ~ ["hello", "world"]
greet.parse("goodbye world")  # returns ~ ["goodbye", "world"]
```


* **Opional** (*`?`*): If a token has a question mark (`?`) at the end then 
it's presence is optional.

```python
from ure.peg import Parser

parser = Parser()
parser.expr["greet"] = '  "goodbye" "cruel"? "world" '

greet = parser.compile("greet")

greet.parse("goodbye world")  # returns ~ ["goodbye", "world"]
greet.parse("goodbye cruel world")  # returns ~ ["goodbye", "cruel", "world"]
```

* **Zero or more** (* `*` *): If a token has a star (`*`) at the end then it can appear none, or infinite number of times.

```python
from ure.peg import Parser

parser = Parser()

parser.expr["num_array"] = ' "[" & number & ("," & number)* & ","? & "]" '

num_array = parser.compile("num_array")

num_array.parse("[1, 3, 4, 56, ]")
# returns ~ ["[", 1, ",", 2, ",", 4, ",", 56, ",", "]"]

num_array.parse("[1, ]")  # returns ~ ["[", 1, ",", "]"]
num_array.parse("[1]")  # returns ~ ["[", 1, "]"]

# does not parse

num_array.parse("[]")
num_array.parse("[0 0]")
num_array.parse("[0; 0]")
```

* **One or more** (*`+`*): If a token ends with a plus sign (`+`) then it hast appear at least one time, or infinite number of times.

```python
from ure.peg import Parser

parser = Parser()
parser.expr["num_array"] = ' "["  number ("," number)+  ","? "]" '

c = parser.compile()

c["num_array"].parseString(
    "[1, 3, 4, 56, ]"
)  # returns ~ ["[", 1, ",", 2, ",", 4, ",", 56, ",", "]"]
c["num_array"].parseString("[1, 2]")  # returns ~ ["[", 1, ",", 2, "]"]


# Does not parse

c["num_array"].parseString("[]")
c["num_array"].parseString("[1]")
c["num_array"].parseString("[0 0]")
c["num_array"].parseString("[0; 0]")
```
* **Ignore** (*`!`*): If a token ends with a exclamation sign (`!`) then will be match but it will not go to the result.

```python
from ure.peg import Parser

parser = Parser()

greet = parser.inline("greet", " /hello/! & /\w+/ ")

result = greet.parse("hello dave")
# Returns <Result ['dave'] {} [0, 10) >

print(f"hola {result.result[0]}")
# prints "hola dave"
```

in that example we hide the word "hello" from the result. A bit more usefull example 
could be parsing a list of numbers, in the form of like [1, 3, .4, 56, -1], allowing trailing commas

```python
from ure import by_name
from ure.peg import Parser

parser = Parser()


@parser.peg(r" @head:( '\['! & number ) & @tail:( ','! & number )* & (','? & ']')!  ")
@by_name()
def na(head, tail):
    return [head[0], *(t[0] for t in tail)]


na.parse("[1, 3, .4, 56, -1]").result

# will return <Result [1.0, 3.0, 0.4, 56.0, -1.0] {} [0, 18) >
```

The group "head" is composed of the expression `( '\['! & number )` that will match "[1", 
but `[` is _ignored_ by using the `!` operation, this means that what would normally return
`["[", 1]` will only return `[1]`. Note that the expression `( '\['! & number )` still means "[" _and_ a number,
 and the _and_ operation resturns an array.

 The group tail is similar as head, but it also has a "zero or more" operation, allowing it to match any (or none) secuence of a comma (`,`) followed by a number. The comma is ommited from the output.

 The final "unamed group" it's the trailing comma group, with the close bracket, "]". This whole group is then ignored, this is there mostly for demostrating purposes, but probably you dont need it since, you dont include that group in the modifier function.

