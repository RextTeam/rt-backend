# RT - hCaptcha

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from aiohttp import ClientSession
from orjson import loads

from .utils import executor_function, json_serialize

if TYPE_CHECKING:
    from .app import TypedSanic


class Response(TypedDict, total=False):
   success: bool
   "is the passcode valid, and does it meet security criteria you specified, e.g. sitekey?"
   challenge_ts: str
   "timestamp of the challenge (ISO format yyyy-MM-dd'T'HH:mm:ssZZ)"
   hostname: str
   "the hostname of the site where the challenge was solved"


class hCaptcha:

    TEST_API_KEY = "0x0000000000000000000000000000000000000000"
    TEST_SITE_KEY = "20000000-ffff-ffff-ffff-000000000002"

    def __init__(self, app: TypedSanic, api_key: str):
        self.app, self.api_key = app, api_key
        self.session = ClientSession(json_serialize=json_serialize)

    @executor_function
    def encrypt(self, session: str) -> str:
        return self.app.ctx.chiper.encrypt(session)

    @executor_function
    def decrypt(self, session: str) -> str:
        return self.app.ctx.chiper.decrypt(session)

    async def verify(self, hcaptcha_response: str) -> Response:
        async with self.session.post(
            "https://hcaptcha.com/siteverify", data={
                "secret": self.api_key,
                "response": hcaptcha_response
            }
        ) as r:
            return await r.json(loads=loads)