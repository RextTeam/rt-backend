# RT - Data

from typing import TypedDict, Any

from sys import argv

from orjson import loads


__all__ = (
    "SECRET", "TEST", "CANARY", "DATA", "REALHOST", "API_VERSION",
    "REALHOST_PORT", "URL", "API_URL"
)


class Secret(TypedDict):
    mysql: dict[str, Any]
    stripe: str
with open("secret.json", "r") as f:
    SECRET: Secret = loads(f.read())


class SanicData(TypedDict):
    host: str
    port: int
    fast: bool
class NormalData(TypedDict):
    sanic: SanicData
    realhost: str
    ips: list
with open("data.json", "r") as f:
    DATA: NormalData = loads(f.read())


CANARY = "canary" in argv
TEST = argv[1] == "test"
REALHOST = DATA["realhost"]


API_VERSION = "0.1.0"


REALHOST_PORT = "{}{}".format(
    REALHOST,
    "" if DATA["sanic"]["port"] in (443, 80)
        else f':{DATA["sanic"]["port"]}'
)
URL = f"http{'s' if DATA['sanic']['port'] == 443 else ''}://{REALHOST_PORT}"
API_URL = URL.replace("://", "://api.", 1)