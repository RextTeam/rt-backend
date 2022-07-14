# RT - Types

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, TypedDict, Any
from collections.abc import Coroutine, Callable
from types import SimpleNamespace

from sanic import Request as OriginalRequest

if TYPE_CHECKING:
    from aiomysql import Pool

    from tempylate import Manager

    from rtlib.common.chiper import ChiperManager
    from rtlib.common.cacher import CacherPool

    from .oauth import OAuthManager
    from .features import Features
    from .app import TypedSanic
    from .customer_manager import CustomerManager
    from .hcaptcha import hCaptchaManager
    from .ipc import ExtendedIpcsServer


__all__ = ("TypedContext", "APIResponseJson", "CoroutineFunction", "Request")


class TypedContext(SimpleNamespace):
    pool: Pool
    rtws: ExtendedIpcsServer
    features: Features
    oauth: OAuthManager
    cachers: CacherPool
    chiper: ChiperManager
    tempylate: Manager
    hcaptcha: hCaptchaManager
    customers: CustomerManager


class APIResponseJson(TypedDict):
    status: int
    message: str
    data: Any
    extras: dict[str, Any]


CoroutineFunction: TypeAlias = Callable[..., Coroutine]


class Request(OriginalRequest):
    app: TypedSanic