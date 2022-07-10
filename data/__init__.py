# RT - Data

from typing import TypedDict, Any

from sys import argv

from itertools import chain

from toml import load


__all__ = (
    "SECRET", "TEST", "DATA", "API_VERSION", "SCHEME", "HOSTS",
    "API_HOSTS", "ORIGINS", "API_ORIGINS", "TIMEOUT", "SSL"
)


class OAuth(TypedDict):
    client_id: str
    client_secret: str
class Secret(TypedDict):
    mysql: dict[str, Any]
    stripe: str
    oauth: OAuth
with open("secret.toml", "r") as f:
    SECRET: Secret = load(f) # type: ignore


class SanicData(TypedDict):
    host: str
    port: int
    fast: bool
class hCaptchaData(TypedDict):
    api_key: str | None
    site_key: str | None
class NormalData(TypedDict):
    sanic: SanicData
    additional_hosts: list[str]
    ssl: bool
    cloudflare: bool
    hcaptcha: hCaptchaData
with open("data.toml", "r") as f:
    DATA: NormalData = load(f) # type: ignore


TEST = argv[1] == "test"
SSL = DATA["ssl"]


def host_port(host: str) -> str:
    return "{}{}".format(
        host,
        "" if DATA["sanic"]["port"] in (443, 80)
            else f':{DATA["sanic"]["port"]}'
    )


SCHEME = f"http{'s' if DATA['sanic']['port'] == 443 else ''}://"
HOSTS = list(map(host_port, chain(("localhost", "127.0.0.1"), DATA["additional_hosts"])))
API_HOSTS = list(map(lambda h: f"api.{h}", HOSTS))
to_url = lambda h: f"{SCHEME}{h}"
ORIGINS = list(map(to_url, HOSTS))
API_ORIGINS = list(map(to_url, API_HOSTS))
del to_url


API_VERSION = "0.1.0"
TIMEOUT = "タイムアウトしました。\nTimeout."