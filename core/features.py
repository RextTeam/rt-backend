# RT - Features

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from asyncio import gather

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("Features",)


class Features:
    "色々な機能をまとめるためのクラスです。"

    def __init__(self, app: TypedSanic):
        self.app = app
        self.app.ctx.rtws.set_route(self.exists)

    async def exists(self, _, mode: Literal["user", "guild", "channel"], id_: int) -> bool:
        """指定されたオブジェクトがRTの見える範囲に存在しているかをチェックします。
        まだBotが起動できていない場合は正しい結果を取得できないことがあります。"""
        return any(await self.app.ctx.rtws.request_all(
            "exists", mode, id_, key=lambda c: c.id_ != "__IPCS_SERVER__"
        ))