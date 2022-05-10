# RT - IPC

from __future__ import annotations

from typing import TYPE_CHECKING

from sanic.server.websockets.impl import WebsocketImplProtocol
from sanic.log import logger
from sanic.request import Request

from ipcs.server import logger as ipcs_logger

from rtlib.common import set_handler

from data import API_HOST

from .utils import is_valid

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("setup",)
set_handler(ipcs_logger)


def setup(app: TypedSanic):
    print(API_HOST)
    @app.websocket("/rtws", API_HOST)
    @is_valid
    async def rtws(_: Request, ws: WebsocketImplProtocol):
        await app.ctx.ipcs.communicate(ws)

    @app.ctx.ipcs.route("logger")
    def logger_(mode: str, *args, **kwargs):
        getattr(logger, mode)(*args, **kwargs)