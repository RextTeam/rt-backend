# RT - IPC

from __future__ import annotations

from typing import TYPE_CHECKING

from sanic.request import Request
from sanic.log import logger
from sanic import Websocket, HTTPResponse

from ipcs import logger as ipcs_logger

from rtlib.common import set_handler

from .utils import is_valid

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("setup",)
set_handler(ipcs_logger)


def setup(app: TypedSanic):
    @app.websocket("/api/rtws")
    @is_valid
    async def rtws(_: Request, ws: Websocket):
        await app.ctx.rtws.communicate(ws)

    @app.route("/test_is_valid")
    @is_valid
    async def test_is_valid(_):
        return HTTPResponse(status=200)

    @app.ctx.rtws.route("logger")
    def logger_(_, mode: str, *args, **kwargs):
        getattr(logger, mode)(*args, **kwargs)

    @app.ctx.rtws.route()
    def ping(_):
        return "pong"