# RT.Backend - OAuth

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Any, overload
from collections.abc import Iterable

from dataclasses import dataclass

from discord.types.user import User

from aiohttp import ClientSession
from orjson import dumps, loads

from .utils import executor_function
from .types_ import Request

from rtlib.common.utils import to_dict_for_dataclass
from rtlib.common.cacher import Cacher

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("PartialUser", "CookieData", "OAuthManager")


class PartialUser(TypedDict):
    id: int
    name: str
    avatar_url: str | None


@dataclass
class CookieData:
    user_id: int
    name: str
    avatar: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CookieData:
        return cls(**data)

    to_dict = to_dict_for_dataclass


class OAuthManager:
    "OAuthクライアントです。一つまでしか作られないべきです。"

    BASE = "https://discord.com/api"

    def __init__(self, app: TypedSanic, client_id: str, client_secret: str):
        self.app = app
        self.app.ctx.oauth = self
        self.session = ClientSession(json_serialize=lambda x: dumps(x).decode()) # type: ignore
        self.states = self.app.ctx.cachers.acquire()
        self.client_id, self.client_secret = client_id, client_secret
        self.urls: Cacher[str, str] = self.app.ctx.cachers.acquire(3600.0)

    async def close(self) -> None:
        "お片付けをします。"
        await self.session.close()

    @executor_function
    def encrypt(self, data: CookieData | dict[str, Any] | bytes) -> str:
        "クッキーデータを暗号化します。"
        if isinstance(data, CookieData):
            data = data.to_dict()
        if isinstance(data, dict):
            data = dumps(data)
        return self.app.ctx.chiper.encrypt_bytes_to_str(data)

    @executor_function
    def decrypt(self, data: str) -> CookieData:
        "暗号化されたクッキーデータを復号化します。"
        return CookieData.from_dict(loads(self.app.ctx.chiper.decrypt_str_to_bytes(data)))

    async def generate_url(self, callback_url: str, scope: Iterable[str]) -> str:
        "OAuthのURLを作ります。一時間程キャッシュとして作ったURLは保管されます。"
        if callback_url not in self.urls:
            async with self.session.get(f"{self.BASE}/oauth2/authorize", params={
                "response_type": "code",
                "scope": "%20".join(scope),
                "client_id": self.client_id,
                "redirect_uri": callback_url
            }) as r:
                self.urls[callback_url] = str(r.url)
        return self.urls[callback_url]

    async def get_token(self, code: str, callback_url: str) -> dict:
        "OAuthから渡されたコードからTOKENを取得します。"
        async with self.session.post(
            f"{self.BASE}/oauth2/token", data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url
            }, headers={"Content-Type": "application/x-www-form-urlencoded"}
        ) as r:
            return await r.json(loads=loads)

    def make_avatar_url(self, user_id: str | int, avatar: str) -> str:
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png"

    @overload
    async def fetch_user(self, token_or_request: str) -> User: ...
    @overload
    async def fetch_user(self, token_or_request: Request) -> PartialUser| None: ...
    async def fetch_user(self, token_or_request: str | Request) -> User | PartialUser | None:
        "ユーザーデータをTOKENまたはリクエストから取得します。"
        if isinstance(token_or_request, str):
            async with self.session.get(
                f"{self.BASE}/v9/users/@me", headers={
                    "Authorization": f"Bearer {token_or_request}"
                }
            ) as r:
                return User(**(await r.json(loads=loads)))
        else:
            if "session" in token_or_request.args or "session" in token_or_request.cookies:
                user = (await self.decrypt(
                    token_or_request.args.get("session")
                    or token_or_request.cookies["session"]
                ))
                return PartialUser(
                    id=user.user_id, name=user.name, avatar_url=None if user.avatar is None
                    else self.make_avatar_url(user.user_id, user.avatar)
                )

    async def make_cookie(self, data: User) -> CookieData:
        "クッキーのデータを作ります。"
        return CookieData(int(data["id"]), data["username"], data["avatar"])