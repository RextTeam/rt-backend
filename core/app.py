# RT - App

from functools import wraps

from sanic.exceptions import Forbidden, SanicException
from sanic.response import HTTPResponse as Response
from sanic.headers import parse_host
from sanic.request import Request
from sanic.log import logger
from sanic import Sanic

from sanic_mysql import ExtendMySQL
from ipcs.ext.for_sanic import SanicIpcsServer

from orjson import JSONDecodeError

from rtlib.common.utils import make_error_message

from data import SECRET, API_VERSION, TEST, CANARY

from .types_ import TypedContext
from .rtws import setup as setup_ipcs
from .features import Features
from .utils import api


__all__ = ("TypedSanic", "setup")


class TypedSanic(Sanic):
    "`ctx`属性の追加型付けがされた`sanic.Sanic`です。"

    ctx: TypedContext


# Poolを作った際にAppのContextにプールを入れておく。
_original_before_server_start_ems = ExtendMySQL.before_server_start
@wraps(_original_before_server_start_ems)
async def _new_before_server_start_ems(self: ExtendMySQL, app, loop):
    await _original_before_server_start_ems(self, app, loop)
    self.app.ctx.pool = self.pool
ExtendMySQL.before_server_start = _new_before_server_start_ems


def setup(app: TypedSanic) -> TypedSanic:
    "Setup app"
    app.ctx.extend_mysql = ExtendMySQL(app, **SECRET["mysql"])
    app.ctx.ipcs = SanicIpcsServer()
    app.ctx.features = Features(app)
    setup_ipcs(app)

    app.config.CORS_ORIGINS = "http://localhost,http://127.0.0.1,https://rt.rext.dev,http://rtbo.tk"
    if TEST:
        app.config.CORS_ORIGINS += ",http://rt-bot-test.com"
    else:
        app.config.REAL_IP_HEADER = "CF-Connecting-IP"
    if CANARY:
        app.config.CORS_ORIGINS += ",http://rt-canary.f5.si"

    app.ext.openapi.describe( # type: ignore
        "RT API",
        version=API_VERSION,
        description="ほとんどのAPIがRTのBotしか使えません。"
    )

    @app.main_process_stop
    async def cleanup(_, __):
        # ipcsサーバーを終了しておく。
        logger.info("Closing ipcs...")
        await app.ctx.ipcs.close(reason="Server is stopping")

    @app.on_request
    async def on_request(request: Request) -> None:
        # ホスト名が許可リストにあるかどうかを調べる。
        host, _ = parse_host(request.host)
        assert host is not None
        host = host.replace("api.", "", 1)
        if f"http://{host}" not in app.config.CORS_ORIGINS and host != "rt.rext.dev":
            raise Forbidden("このアドレスでアクセスすることはできません。")

    @app.exception(Exception)
    async def on_exception(_: Request, exception: Exception) -> Response:
        if isinstance(exception, SanicException):
            return api(exception.message, "Error", exception.status_code)
        if isinstance(exception, AssertionError):
            status = 400
            data = exception.args[0]
        else:
            if isinstance(exception, JSONDecodeError):
                status = 400
            else:
                status = 500
            logger.error("Error was occured:\n%s" % make_error_message(exception))
            data = f"{exception.__class__.__name__}: {exception}"
        return api(data, "Error", status)

    return app