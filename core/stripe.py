# RT - Stripe

from __future__ import annotations

from typing import TYPE_CHECKING

from sanic import Blueprint, Request, HTTPResponse

from async_stripe import stripe
from stripe.error import SignatureVerificationError

from data import API_HOSTS

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("StripeManager",)


class StripeManager:
    def __init__(self, app: TypedSanic, secret: str):
        self.app, self.secret = app, secret
        self.app.add_route(self.webhook, "/payments/webhook", host=API_HOSTS)
        @self.app.route("/test", host="api.localhost:8080")
        async def test(request):
            return HTTPResponse(status=200)
        print(1, API_HOSTS)

    @staticmethod
    def get_blueprint() -> Blueprint:
        return Blueprint("payments", "/payments", API_HOSTS)

    async def webhook(self, request: Request) -> HTTPResponse:
        # ウェブフックのリクエストがStripeからであることを確かめる。
        try:
            await stripe.Webhook.construct_event(
                request.body, request.headers["HTTP_STRIPE_SIGNATURE"],
                self.secret
            ) # type: ignore
        except (SignatureVerificationError, ValueError):
            return HTTPResponse(status=400)

        return HTTPResponse(status=200)