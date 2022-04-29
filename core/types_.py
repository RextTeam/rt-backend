# RT - Types

from typing import TypedDict, Any
from types import SimpleNamespace

from sanic_mysql import ExtendMySQL
from aiomysql import Pool

from ipcs.ext.for_sanic import SanicIpcsServer

from .features import Features


__all__ = ("TypedContext", "APIResponseJson")


class TypedContext(SimpleNamespace):
    extend_mysql: ExtendMySQL
    pool: Pool
    ipcs: SanicIpcsServer
    features: Features


class APIResponseJson(TypedDict):
    status: int
    message: str
    data: Any
    extras: dict[str, Any]