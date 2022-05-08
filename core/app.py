# RT - App

from functools import wraps

from sanic.response import HTTPResponse as Response, html, redirect
from sanic.exceptions import Forbidden, SanicException
from sanic.headers import parse_host
from sanic.request import Request
from sanic.log import logger
from sanic import Sanic

from sanic_mysql import ExtendMySQL
from ipcs.ext.for_sanic import SanicIpcsServer
from miko import Manager

from orjson import JSONDecodeError

from rtlib.common.utils import make_error_message
from rtlib.common.chiper import ChiperManager
from rtlib.common.cacher import CacherPool

from data import REALHOST, REALHOST_PORT, SECRET, DATA, API_VERSION, TEST, CANARY

from .types_ import TypedContext
from .rtws import setup as setup_ipcs
from .oauth import OAuth
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
    app.ctx.chiper = ChiperManager.from_key_file("secret.key")
    app.ctx.miko = Manager()
    setup_ipcs(app)

    def t(tag="div", extends="", class_="", **kwargs) -> str:
        "複数言語対応用"
        return "".join(
            f'<{tag} class="language {key} {class_}" {extends} hidden>{value}</{tag}>'
            for key, value in kwargs.items()
        )
    app.ctx.miko.extends["t"] = t

    async def layout(**kwargs):
        kwargs.setdefault("head", "")
        kwargs.setdefault("content", "")
        return await app.ctx.miko.aiorender("rt-frontend/layout.html", **kwargs)
    app.ctx.miko.extends["layout"] = layout

    if not TEST and not CANARY:
        app.config.REAL_IP_HEADER = "CF-Connecting-IP"

    app.config.CORS_ORIGINS = DATA["origins"]
    app.ext.openapi.describe( # type: ignore
        "RT API",
        version=API_VERSION,
        description="ほとんどのAPIがRTのBotしか使えません。"
    )

    @app.route("/")
    async def redirect_index(request: Request):
        return redirect("/index.html")

    @app.main_process_start
    async def on_start(_, __):
        app.ctx.cachers = CacherPool()

    @app.before_server_start
    async def on_start_server(app_: TypedSanic, __):
        app_.ctx.oauth = OAuth(app_, **SECRET["oauth"])

    @app.main_process_stop
    async def cleanup(_, __):
        # ipcsサーバーを終了しておく。
        logger.info("Closing cacher...")
        app.ctx.cachers.close()
        logger.info("Closing ipcs...")
        await app.ctx.ipcs.close(reason="Server is stopping")

    @app.on_request
    async def on_request(request: Request):
        # ホスト名が許可リストにあるかどうかを調べる。
        host, _ = parse_host(request.host)
        assert host is not None
        host = host.replace("api.", "", 1)
        if host != REALHOST:
            raise Forbidden("このアドレスでアクセスすることはできません。")

        if "api." not in request.host and request.url.endswith(".html"):
            path = request.path
            if path.startswith("/"):
                path = path[1:]
            return html(await app.ctx.miko.aiorender(f"rt-frontend/{path}", t=t))

    @app.exception(Exception)
    async def on_exception(_: Request, exception: Exception) -> Response:
        data = f"{exception.__class__.__name__}: {exception}"
        if isinstance(exception, AssertionError):
            status = 400
            data = exception.args[0]
        elif isinstance(exception, SanicException):
            status = exception.status_code
        else:
            if isinstance(exception, JSONDecodeError):
                status = 400
            else:
                status = 500
        if status == 500:
            logger.error("Error was occured:\n%s" % make_error_message(exception))
        return api(data, "Error", status)

    app.static("/", "rt-frontend", host=REALHOST_PORT)
    app.static("/favicon.ico", "rt-frontend/img/favicon.ico")

    from blueprints import bp
    app.blueprint(bp)
    from blueprints.oauth import bp
    app.blueprint(bp)

    return app