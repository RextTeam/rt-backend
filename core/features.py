# RT - Features

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from discord.ext import tasks
from sanic import HTTPResponse

from data import DATA, TEST

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("Features",)


class Features:
    "色々な機能をまとめるためのクラスです。"

    def __init__(self, app: TypedSanic):
        self.app = app
        self.shard_count = DATA["shard_count"]
        self.app.ctx.rtws.set_route(self.exists)
        @self.app.ctx.rtws.listen()
        async def on_close(_, __):
            self.tell_busy.cancel()
        @self.app.ctx.rtws.listen()
        async def on_ready():
            self.tell_busy.start()
        if TEST:
            @self.app.route("/tell_busy")
            async def tell_busy(_):
                await self.tell_busy()
                return HTTPResponse("Ok")

    @tasks.loop(minutes=15)
    async def tell_busy(self):
        # 一番忙しくないシャードを持っているやつを探して、忙しくないから何かやれと伝える。
        tasks = {}
        for key in self.app.ctx.rtws.connections.keys():
            if self._without_self(self.app.ctx.rtws.connections[key]):
                tasks[key] = self.app.loop.create_task(
                    self.app.ctx.rtws.connections[key].request("get_all_tasks_quantity"),
                    name="get_all_tasks_quantity: %s"  % key
                )
        for index, (_, key) in enumerate(sorted({
            (await task, key)
            for key, task in tasks.items()
        }, key=lambda x: x[0])):
            await self.app.ctx.rtws.connections[key].request("you_are", index != 0)

    def calculate_shard(self, guild_id: int) -> int:
        "サーバーのIDからシャードIDを計算します。"
        return (guild_id >> 22) % self.shard_count

    def _without_self(self, c):
        return c.id_ != "__IPCS_SERVER__"

    async def exists(self, _, mode: Literal["user", "guild", "channel"], id_: int) -> bool:
        """指定されたオブジェクトがRTの見える範囲に存在しているかをチェックします。
        まだBotが起動できていない場合は正しい結果を取得できないことがあります。"""
        return not self.shard_count or len(self.app.ctx.rtws.connections)-1 != self.shard_count \
            or any(await self.app.ctx.rtws.request_all(
                "exists", mode, id_, key=self._without_self
            ))