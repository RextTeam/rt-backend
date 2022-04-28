# RT - Utils

from typing import TypeVar, Any
from collections.abc import Callable, Coroutine

from functools import wraps

from sanic.exceptions import Forbidden
from sanic.request import Request

from data import DATA


IvFnT = TypeVar("IvFnT", bound=Callable[..., Coroutine])
def is_valid(route: IvFnT) -> IvFnT:
    @wraps(route)
    async def _new(request: Request, *args, **kwargs) -> Any:
        if request.remote_addr in DATA["ips"]:
            return await route(request, *args, **kwargs)
        else:
            raise Forbidden("Your IP is not an accessible IP for this endpoint.")
    return _new # type: ignore