# RT - Ipc

from __future__ import annotations

from typing import TYPE_CHECKING

from ipcs.ext.for_sanic import ServerForSanic

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("ExtendedIpcsServer",)


class ExtendedIpcsServer(ServerForSanic):
    "シャードを特定するための関数を実装したIPCSサーバークラスです。"

    app: TypedSanic

    def detect_target(self, guild_id: int) -> str:
        "ギルドIDの監視対象のシャードのIDを取得します。"
        ids = set(self.app.ctx.features.shard_ids)
        if "None" in ids:
            return "None"
        else:
            return str((guild_id >> 22) % self.app.ctx.features.shard_count)