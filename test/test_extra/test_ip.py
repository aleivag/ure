import pytest
from ipaddress import IPv4Address, IPv6Address, ip_address
from ure.extra import IPv4, IPv6, IP

ipv4s = ["0.0.0.0", "192.168.0.1", "255.255.255.255"]
ipv6s = [
    "::",
    "FF01::101",
    "::1",
    "2001:DB8::8:800:200C:417A",
    "0:0:0:0:0:0:0:0",
    "2001:DB8:0:0:8:800:200C:417A",
    "0:0:0:0:0:0:13.1.68.3",
    "0:0:0:0:0:FFFF:129.144.52.38",
    "0:0:0:0:0:0:13.1.68.3",
    "0:0:0:0:0:FFFF:129.144.52.38",
    "::13.1.68.3",
    "::FFFF:129.144.52.38",
    "2001:db8:3:4::192.0.2.33",
    "64:ff9b::192.0.2.33",
]


@pytest.mark.parametrize("ip", ipv4s)
def test_ipv4(ip):
    assert IPv4Address(ip) == IPv4.parse(ip).result


@pytest.mark.parametrize("ip", ipv6s)
def test_ipv6(ip):
    assert IPv6Address(ip) == IPv6.parse(ip).result


@pytest.mark.parametrize("ip", ipv6s + ipv4s)
def test_ipv6(ip):
    assert ip_address(ip) == IP.parse(ip).result
