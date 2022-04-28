# RT - Types

from types import SimpleNamespace

from sanic_mysql import ExtendMySQL
from aiomysql import Pool

from ipcs import IpcsServer


__all__ = ("TypedContext",)


class TypedContext(SimpleNamespace):
    extend_mysql: ExtendMySQL
    pool: Pool
    ipcs: IpcsServer