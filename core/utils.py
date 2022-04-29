# RT - Utils

from typing import TypeVar, Literal, Any
from collections.abc import Callable, Coroutine

from functools import wraps

from sanic.exceptions import Forbidden
from sanic.response import HTTPResponse
from sanic.request import Request

from orjson import dumps

from data import DATA

from .types_ import APIResponseJson


__all__ = ("is_valid", "get_ip", "api")


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