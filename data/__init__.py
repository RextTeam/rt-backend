# RT - Data

from typing import TypedDict, Any

from sys import argv

from orjson import loads


__all__ = (
    "SECRET", "TEST", "CANARY", "DATA", "REALHOST", "API_VERSION",
    "REALHOST_PORT", "URL", "API_URL", "API_HOSTS", "TIMEOUT", "SSL"
)


class OAuth(TypedDict):
    client_id: str
    client_secret: str
class Secret(TypedDict):
    mysql: dict[str, Any]
    stripe: str
    oauth: OAuth
with open("secret.json", "r") as f:
    SECRET: Secret = loads(f.read())


class SanicData(TypedDict):
    host: str
    port: int
    fast: bool
class hCaptchaData(TypedDict, total=False):
    api_key: str
    site_key: str
class NormalData(TypedDict):
    sanic: SanicData
    realhost: str
    origins: str
    ips: list
    ssl: bool
    hcaptcha: hCaptchaData
with open("data.json", "r") as f:
    DATA: NormalData = loads(f.read())


CANARY = "canary" in argv
TEST = argv[1] == "test"
REALHOST = DATA["realhost"]
SSL = DATA["ssl"]


def host_port(host: str) -> str:
    return "{}{}".format(
        host,
        "" if DATA["sanic"]["port"] in (443, 80)
            else f':{DATA["sanic"]["port"]}'
    )


API_HOSTS = list(map(host_port, (f"api.{REALHOST}", "api.localhost", "api.127.0.0.1")))
API_VERSION = "0.1.0"
REALHOST_PORT = host_port(REALHOST)
URL = f"http{'s' if DATA['sanic']['port'] == 443 else ''}://{REALHOST_PORT}"
API_URL = URL.replace("://", "://api.", 1)


TIMEOUT = "タイムアウトしました。\nTimeout."