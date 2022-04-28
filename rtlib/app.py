# RT - App

from functools import wraps

from sanic import Sanic

from sanic_mysql import ExtendMySQL
from ipcs import IpcsServer

from .types_ import TypedContext


__all__ = ("TypedSanic", "setup")


class TypedSanic(Sanic):
    ctx: TypedContext


# Poolを作った際にAppのContextにプールを入れておく。
_original_before_server_start_ems = ExtendMySQL.before_server_start
@wraps(_original_before_server_start_ems)
async def _new_before_server_start_ems(self: ExtendMySQL, *args, **kwargs):
    await _original_before_server_start_ems(self, *args, **kwargs)
    self.app.ctx.pool = self.pool
ExtendMySQL.before_server_start = _new_before_server_start_ems


def setup(app: TypedSanic) -> TypedSanic:
    "Setup app"
    app.ctx.extend_mysql = ExtendMySQL(app)
    app.ctx.ipcs = IpcsServer()
    return app