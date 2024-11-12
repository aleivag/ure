from ure.peg import Parser
from ure import by_result
import pytest


PS_AUX = """\
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   1108     4 ?        Ss   15:54   0:00 /mnt/shared/sbin/tini -- /mnt/shared/sbin/micro-inetd 22 /mnt/shared/s
root           7  0.0  0.0   4056   188 ?        S+   15:54   0:00 /mnt/shared/sbin/micro-inetd 22 /mnt/shared/sbin/dropbear -i -s -m -R
root         272  0.4  0.0  19380  2132 ?        Rs   15:54   0:00 /mnt/shared/sbin/dropbear -i -s -m -R
ubuntu       273  5.1  0.0 1250936 51952 ?       Sl   15:54   0:00 vfs-worker {"pingInterval":5000,"nodePath":"/mnt/shared/lib/node_modul
ubuntu       749  0.0  0.0  11380  3044 ?        S    15:54   0:00 bash -c #!/usr/bin/env bash # Helper script to launch jedi/pylint in a
ubuntu       757  2.0  0.0 196704 21032 ?        S    15:54   0:00 /mnt/shared/lib/python2/bin/python2 -c import argparse import jedi imp
ubuntu       815  0.0  0.0 123740  2616 pts/1    Ss+  15:54   0:00 /mnt/shared/sbin/tmux -u2 -L cloud92.2 new -s aleivag1@parsing_913 exp
ubuntu       818  0.0  0.0 132568  3388 ?        Rs   15:54   0:00 /mnt/shared/sbin/tmux -u2 -L cloud92.2 new -s aleivag1@parsing_913 exp
ubuntu       819  0.0  0.0  11260  2672 pts/2    Ss   15:54   0:00 bash -c export ISOUTPUTPANE=0;bash -l
ubuntu       820  5.0  0.0  29160 12940 pts/2    S    15:54   0:00 bash -l
ubuntu      1283  0.0  0.0  17256  2388 pts/2    R+   15:54   0:00 ps aux"""


parser = Parser()


parser.expr.update(
    {
        "header": """
            'USER' & 'PID' & '%CPU' & '%MEM' & 'VSZ' &
            'RSS' & 'TTY'  & 'STAT' & 'START' & 'TIME' & 
            'COMMAND'
        """,
        # line def
        "user": r"/\w+/",
        "tty": r'"\?" | ("pts/\d+")',
        "stat": r"/\w+\+?/",
        "start": r"/\d\d\d\d|\d\d?:\d\d/",
        "time": r"/\d\d?:\d\d|\w{3}\d+/",
        "cmdline": "/.+/",
        "ps": "header! & @process:process_line+",
        "ews": '" "*!',
    }
)


@parser.peg(
    """
        @user:user & @pid:integer & @cpu:number & @mem:number & 
        @vsz:integer & @rss:integer & @tty:tty & @stat:stat & 
        @start:start & @time:time & @cmdline:cmdline
    """,
    # number number tty stat time  time @cli:cmdline
    decorator=by_result,
)
def process_line(result):
    return result.names


def test_ps_aux_compile_header():
    header = parser.compile("header")
    r = header.parse(PS_AUX.splitlines()[0])
    # An expression like " a & b & c & d " is parsed the same as
    # like " a & (b & (c & d)) "

    assert r.result == [
        "USER",
        [
            "PID",
            [
                "%CPU",
                [
                    "%MEM",
                    [
                        "VSZ",
                        [
                            "RSS",
                            [
                                "TTY",
                                [
                                    "STAT",
                                    [
                                        "START",
                                        [
                                            "TIME",
                                            "COMMAND",
                                        ],
                                    ],
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ],
    ]


@pytest.mark.parametrize("ln", PS_AUX.splitlines()[1:])
def test_ps_aux_compile_one_token(ln):
    r = process_line.parse(ln).result
    assert isinstance(r, dict)
    assert r["user"] in ["root", "ubuntu"]


def test_ps():
    ps = parser.compile("ps")
    r = ps.parse(PS_AUX).names["process"]
    assert len(r) == len(PS_AUX.splitlines()) - 1
