# RT - Data

from typing import TypedDict

from sys import argv

from orjson import loads


__all__ = ("SECRET", "TEST", "DATA", "get_realhost_port", "get_url")


class Secret(TypedDict):
    stripe: str
with open("secret.json", "r") as f:
    SECRET: Secret = loads(f.read())


class SanicData(TypedDict, total=False):
    host: str
    port: int
    fast: bool
class NormalData(TypedDict):
    sanic: SanicData
    ips: list
with open("data.json", "r") as f:
    DATA: NormalData = loads(f.read())


if argv[1] == "test":
    TEST = True
    REALHOST = DATA["sanic"].get("host", "")
else:
    TEST = False
    REALHOST = "rt.rext.dev"


def get_realhost_port() -> str:
    "HOSTとPORTが繋げられた文字列を取得します。"
    return "{}{}".format(
        REALHOST,
        "" if DATA["sanic"].get("port", 80) in (443, 80)
            else DATA['sanic'].get('host', "")
    )


def get_url() -> str:
    "URLを取得します。"
    return f"http{'s' if DATA['sanic'].get('port', 0) == 443 else ''}://{get_realhost_port()}/"