# RT - Utils

from __future__ import annotations

from typing import TypeVar, ParamSpec, Literal, Any
from collections.abc import Callable, Coroutine

from functools import wraps
from time import time

from sanic.exceptions import Forbidden, SanicException
from sanic.response import HTTPResponse

from aiofiles.os import wrap as _wrap # type: ignore
from orjson import dumps

from data import DATA

from .types_ import APIResponseJson, Request


__all__ = ("is_valid", "get_ip", "api", "executor_function", "CoolDown", "json_serialize")


EfArgsP, EfRetT = ParamSpec("EfArgsP"), TypeVar("EfRetT")
def executor_function(func: Callable[EfArgsP, EfRetT]) \
        -> Callable[EfArgsP, Coroutine[Any, Any, EfRetT]]:
    "同期関数を`loop.run_in_executor`で自動で実行されるようにします。"
    return _wrap(func)


IvFnT = TypeVar("IvFnT", bound=Callable[..., Coroutine])
def is_valid(route: IvFnT) -> IvFnT:
    "リクエスト元のIPがコアAPIにアクセス可能かどうかを調べるためのデコレータです。"
    @wraps(route)
    async def _new(request: Request, *args, **kwargs) -> Any:
        if get_ip(request) in DATA["ips"]:
            return await route(request, *args, **kwargs)
        else:
            raise Forbidden("Your IP is not an accessible IP for this endpoint.")
    return _new # type: ignore


def get_ip(request: Request) -> str:
    "リクエストからIPを取り出します。"
    return request.remote_addr or request.ip


def api(
    data: Any, message: Literal["Ok", "Error"] = "Ok", status: int = 200,
    headers: Any = None, content_type: str = "application/json", **kwargs
) -> HTTPResponse:
    "API用のJSON形式のレスポンスを作ります。"
    return HTTPResponse(
        dumps(APIResponseJson(status=status, message=message, data=data, extras=kwargs)),
        status, headers, content_type
    )


class CoolDown:
    "細かくレート制限をRouteにかけたい際に使えるデコレータの名を持つクラスです。"

    rate: int
    per: float
    cache_max: int
    message: str
    strict: bool
    max_per: float
    cache: dict[str, tuple[int, float]]
    func: Callable[..., Coroutine]
    get_key: Callable[[Request], str]

    def __new__(
        cls, rate: int, per: float, message: str = "Too many requests.", wrap_html: bool = False,
        cache_max: int = 1000, strict: bool = True, max_per: float | None = None,
        get_key: Callable[[Request], str] = get_ip
    ) -> Callable[[Callable[..., Coroutine]], CoolDown]:
        self = super().__new__(cls)
        self.rate, self.per, self.strict = rate, per, strict
        self.cache_max, self.message = cache_max, message
        self.max_per = max_per or per * cache_max // 100
        self.cache = {}
        self.get_key = get_key

        def decorator(func):
            self.func = func
            return wraps(func)(self)

        return decorator

    async def _async_call(self, request, *args, **kwargs):
        key = self.get_key(request)
        before = self.cache.get(key, (0, (now := time()) + self.per))
        self.cache[key] = (before[0] + 1, before[1])
        if self.cache[key][1] > now:
            if self.cache[key][0] > self.rate:
                if self.strict and self.cache[key][1] < self.max_per:
                    self.cache[key] = (self.cache[key][0], self.cache[key][1] + self.per)
                raise SanicException(
                    self.message.format(self.cache[key][1] - now), 429
                )
        else:
            del self.cache[key]
        return await self.func(request, *args, **kwargs)

    def __call__(self, request: Request, *args, **kwargs):
        # もしキャッシュが最大数になったのならcacheで一番古いものを削除する。
        if len(self.cache) >= self.cache_max:
            del self.cache[max(list(self.cache.items()), key=lambda d: d[1][1])[0]]
        # 非同期で実行できるようにコルーチン関数を返す。
        return self._async_call(request, *args, **kwargs)


json_serialize = lambda x: dumps(x).decode()