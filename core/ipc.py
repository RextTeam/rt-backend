# RT - Ipc

from collections.abc import Iterator

from ipcs.ext.for_sanic import ServerForSanic


__all__ = ("ExtendedIpcsServer",)


class ExtendedIpcsServer(ServerForSanic):
    "シャードを特定するための関数を実装したIPCSサーバークラスです。"

    def detect_target(self, guild_id: int) -> str:
        "ギルドIDの監視対象のシャードのIDを取得します。"
        ids = set(self.shard_ids)
        if "None" in ids:
            return "None"
        else:
            return str((guild_id >> 22) % len(ids))

    @property
    def shard_ids(self) -> Iterator[str]:
        "シャードのIDのリストを返します。"
        return (
            id_ for id_ in self.connections.keys()
            if id_ != "__IPCS_SERVER__"
        )