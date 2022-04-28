# RT - IPC

from __future__ import annotations

from typing import TYPE_CHECKING

from sanic.server.websockets.impl import WebsocketImplProtocol
from sanic.request import Request

from data import REALHOST

if TYPE_CHECKING:
    from .app import TypedSanic


def setup(app: TypedSanic):
    @app.websocket("/rtws", f"api.{REALHOST}")
    async def rtws(_: Request, ws: WebsocketImplProtocol):
        await app.ctx.ipcs.communicate(ws) # type: ignore