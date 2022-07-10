# RT - App

from functools import wraps

from sanic.response import HTTPResponse, html, redirect
from sanic.exceptions import Forbidden, SanicException
from sanic.errorpages import HTMLRenderer
from sanic.headers import parse_host
from sanic.request import Request
from sanic.log import logger
from sanic import Sanic

from sanic_mysql import ExtendMySQL
from tempylate import Manager

from orjson import JSONDecodeError

from rtlib.common.utils import make_error_message
from rtlib.common.chiper import ChiperManager
from rtlib.common.cacher import CacherPool

from data import SECRET, DATA, API_VERSION, TEST, SSL, HOSTS, API_HOSTS, ORIGINS, API_ORIGINS

from .types_ import TypedContext
from .rtws import setup as setup_ipcs
from .oauth import OAuthManager
from .hcaptcha import hCaptchaManager
from .stripe import StripeManager
from .ipc import ExtendedIpcsServer
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
_original_request_url_for = Request.url_for
@wraps(_original_request_url_for)
def _new_request_url_for(*args, **kwargs) -> str:
    data = _original_request_url_for(*args, **kwargs)
    if SSL and data.startswith("http://"):
        data = data.replace("http://", "https://", 1)
    return data
Request.url_for = _new_request_url_for


def setup(app: TypedSanic) -> TypedSanic:
    "Setup app"
    app.ctx.extend_mysql = ExtendMySQL(app, **SECRET["mysql"])
    app.ctx.ipcs = ExtendedIpcsServer()
    app.ctx.features = Features(app)
    app.ctx.chiper = ChiperManager.from_key_file("secret.key")
    app.ctx.tempylate = Manager({"app": app})
    setup_ipcs(app)

    # フロントエンド向けのセットアップをする。
    def t(tag="div", extends="", class_="", **kwargs) -> str:
        "複数言語対応用"
        return "".join(
            f'<{tag} class="language {key} {class_}" {extends} hidden>{value}</{tag}>'
            for key, value in kwargs.items()
        )
    app.ctx.tempylate.builtins["t"] = t

    async def layout(**kwargs):
        kwargs.setdefault("head", "")
        kwargs.setdefault("content", "")
        return await app.ctx.tempylate.aiorender_from_file(
            "rt-frontend/layout.html", **kwargs
        )
    app.ctx.tempylate.builtins["layout"] = layout

    # バックエンド向けのセットアップをする。
    if DATA["cloudflare"]:
        app.config.REAL_IP_HEADER = "CF-Connecting-IP"

    app.config.CORS_ORIGINS = ORIGINS + API_ORIGINS
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
        app.ctx.cachers.start()
        app.ctx.stripe = StripeManager(app, SECRET["stripe"])

    @app.before_server_start
    async def on_start_server(app_: TypedSanic, __):
        app.ctx.hcaptcha = hCaptchaManager(
            app, DATA["hcaptcha"]["api_key"] or hCaptchaManager.TEST_API_KEY,
            DATA["hcaptcha"]["site_key"] or hCaptchaManager.TEST_SITE_KEY
        )
        app_.ctx.oauth = OAuthManager(app_, **SECRET["oauth"])

    @app.main_process_stop
    async def cleanup(_, __):
        # ipcsサーバーを終了しておく。
        logger.info("Closing cacher...")
        app.ctx.cachers.close()
        logger.info("Closing ipcs...")
        await app.ctx.ipcs.close(reason="Server is stopping")

    @app.on_request
    async def on_request(request: Request) -> HTTPResponse | None:
        # ホスト名が許可リストにあるかどうかを調べる。
        if request.host not in HOSTS and request.host not in API_HOSTS:
            raise Forbidden("このアドレスでアクセスすることはできません。")

        if "api." not in request.host and request.url.endswith(".html"):
            path = request.path
            if path.startswith("/"):
                path = path[1:]
            return html(await app.ctx.tempylate.aiorender_from_file(f"rt-frontend/{path}"))

    @app.exception(Exception)
    async def on_exception(request: Request, exception: Exception) -> HTTPResponse:
        if "api." in request.host:
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
        else:
            return HTMLRenderer(request, exception, TEST).render()

    for host in HOSTS:
        app.static("/", "rt-frontend", host=host)
    app.static("/favicon.ico", "rt-frontend/img/favicon.ico")

    return app