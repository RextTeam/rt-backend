# RT - Features

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from data import DATA

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("Features",)


class Features:
    "色々な機能をまとめるためのクラスです。"

    def __init__(self, app: TypedSanic):
        self.app = app
        self.shard_count = len(DATA["shard_ids"])
        self.shard_ids = DATA["shard_ids"]
        self.app.ctx.rtws.set_route(self.exists)

    def calculate_shard(self, guild_id: int) -> int:
        "サーバーのIDからシャードIDを計算します。"
        return (guild_id >> 22) % self.shard_count

    async def exists(self, _, mode: Literal["user", "guild", "channel"], id_: int) -> bool:
        """指定されたオブジェクトがRTの見える範囲に存在しているかをチェックします。
        まだBotが起動できていない場合は正しい結果を取得できないことがあります。"""
        return any(await self.app.ctx.rtws.request_all(
            "exists", mode, id_, key=lambda c: c.id_ != "__IPCS_SERVER__"
        ))