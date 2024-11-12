from ure.peg import Parser
from ure import extract_name, by_name, by_result, Base, regex
import re
import pytest
from ipaddress import ip_address, IPv6Address, IPv4Address

status = """/10.1.2.4
  generation:0
  heartbeat:0
/10.1.2.3
  generation:0
  heartbeat:0
/10.1.2.6
  generation:1444263348
  heartbeat:6232
  LOAD:2.0293227179E10
  INTERNAL_IP:10.26.81.97
  DC:DC1
  STATUS:NORMAL,-1041938454866204344
  HOST_ID:36fdcf57-0274-43b8-a501-c0e475e3e30b
  X_11_PADDING:{"workload":"Cassandra","active":"true"}
  RPC_ADDRESS:10.26.81.97
  RACK:RAC1
  SCHEMA:ce2a34e3-0967-34ea-ad55-10270b805218
  NET_VERSION:7
  RELEASE_VERSION:2.0.12.275
  SEVERITY:0.0
/10.1.2.5
  generation:0
  heartbeat:0"""


end_of_line = Base(re.compile(r"$", re.MULTILINE), ws=None)


parser = Parser()
gen_kv = by_name(lambda key, value: (key, value))
parser.expr.update(
    {
        "eol": end_of_line,
        "hostinfostart": ('"/"! & @ip:ip_address ', by_name(lambda ip: ip)),
        "key": r"/[\w_\d]+/",
        "value": (
            r"(@val:ip_address & eol) | (@val:number & eol) | @val:/.+/",
            extract_name("val"),
        ),
        "kv": (
            r"@key:key & /:/ & @value:value",
            gen_kv,
        ),
        "gossiphostinfo": "hostinfostart &  kv+",
    }
)


@parser.peg("gossiphostinfo+")
@by_result()
def gossip_status(result):
    return {h: {k: v for k, v in g} for h, g in result.result}


@pytest.mark.parametrize(
    "head", [line for line in status.splitlines() if line.startswith("/")]
)
def test_goosip_hostinfostart(head):
    hostinfostart = parser.compile("hostinfostart")

    assert hostinfostart.parse(head).result == ip_address(head.lstrip("/"))


@pytest.mark.parametrize(
    "nkv", [line for line in status.splitlines() if not line.startswith("/")]
)
def test_goosip_kv(nkv):
    hostinfostart = parser.compile("kv")

    assert (
        hostinfostart.parse(nkv).result[0]
        == tuple(k.lstrip() for k in nkv.split(":", 1))[0]
    )

    if hostinfostart.parse(nkv).result[0] in ("generation", "heartbeat"):
        assert isinstance(hostinfostart.parse(nkv).result[1], int)

    if hostinfostart.parse(nkv).result[0] in ("RPC_ADDRESS", "INTERNAL_IP"):
        assert isinstance(
            hostinfostart.parse(nkv).result[1], (IPv6Address, IPv4Address)
        )


def test_goosip_gossiphostinfo():
    result = gossip_status.parse(status).result

    assert list(result.keys()) == [
        ip_address(line.lstrip("/"))
        for line in status.splitlines()
        if line.startswith("/")
    ]
