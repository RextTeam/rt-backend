# RT - Customer Manager

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, Literal

from time import time

from sanic import Blueprint, Request, HTTPResponse
from sanic.log import logger

from ipcs import ConnectionForServer

from discord.ext import tasks

from async_stripe import stripe
from stripe.error import SignatureVerificationError

from rtlib.common.reply_error import BadRequest
from rtlib.common.database import DatabaseManager

if TYPE_CHECKING:
    from .app import TypedSanic


__all__ = ("CustomerManager", "PeriodMode", "PaymentLinkContainer")


class CustomerManager:
    "製品版の購入をした人を管理したりするためのクラスです。"

    def __init__(self, app: TypedSanic, api_key: str, endpoint_secret: str):
        self.app, self.api_key, self.endpoint_secret = app, api_key, endpoint_secret
        self.app.add_route(
            self.webhook, "/api/payments/webhook",
            ("POST", "GET")
        )
        stripe.api_key = self.api_key

    PERIOD_SECONDS = {
        "year": 31536000,
        "month": 2592000 + 86400 * 4,
        "day": 86400
    }

    async def start(self) -> None:
        "最初に呼ぶべき関数です。データベースにテーブルを作ります。"
        async with self.app.ctx.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Customers (
                        GuildId BIGINT PRIMARY KEY NOT NULL,
                        UserId BIGINT, Deadline DOUBLE
                    );"""
                )
        self._check_dead.start()

    def close(self) -> None:
        "お片付けをします。Botの終了時に呼ぶべきです。"
        self._check_dead.cancel()

    @tasks.loop(minutes=1)
    async def _check_dead(self):
        # 製品版の期限が切れているユーザーを探す。
        # もし、期限が切れているのなら、製品版ユーザーとして扱わないようにする。
        now = time()
        async with self.app.ctx.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                async for row in DatabaseManager.fetchstep(cursor, "SELECT * FROM Customers;"):
                    if row[2] <= now:
                        connection = self.app.ctx.rtws.connections \
                            [self.app.ctx.rtws.detect_target(row[0])]
                        assert isinstance(connection, ConnectionForServer)
                        if connection.ws.closed:
                            continue
                        await connection.request("remove_customer_cache", row[0])
                        await cursor.execute(
                            "DELETE FROM Customers WHERE GuildId = %s AND UserId = %s LIMIT 1;",
                            row[:-1]
                        )

    @staticmethod
    def get_blueprint() -> Blueprint:
        return Blueprint("payments", "/api/payments")

    async def webhook(self, request: Request) -> HTTPResponse:
        # ウェブフックのリクエストがStripeからであることを確かめる。
        if "stripe-signature" not in request.headers:
            raise BadRequest("Stripe's signature header is not contained in headers.")
        try:
            event: stripe.Event = stripe.Webhook.construct_event(
                request.body, request.headers["stripe-signature"],
                self.endpoint_secret
            )
        except (SignatureVerificationError, ValueError):
            return HTTPResponse(status=400)

        if event["type"] == "checkout.session.completed":
            # 誰による決済なのか、月額か年額かを取り出す。その情報は暗号化して`client_reference_id`に入れている。
            try:
                user_id, guild_id, period, _ = self.app.ctx.chiper.decrypt(
                    event["data"]["object"]["client_reference_id"]
                ).split("_")
            except Exception as e:
                logger.warning("Failed to decrypt `client_reference_id` of someone's payment processing: %s" % e)
                return HTTPResponse(status=400)
            # 支払いが済んだのなら有料ユーザーの一員とする。
            deadline = time() + self.PERIOD_SECONDS[period]
            async with self.app.ctx.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO Customers VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE UserId = %s, Deadline = %s;""",
                        (int(guild_id), user_id, deadline, user_id, deadline)
                    )

        return HTTPResponse(status=200)


PeriodMode: TypeAlias = Literal["year", "month", "day"]
class PaymentLinkContainer:
    def __init__(self, app: TypedSanic, payment_links: dict[str, str]):
        self.app, self.payment_links = app, payment_links

    def get_link(self, period_mode: PeriodMode, user_id: int | str, guild_id: int | str) -> str:
        "製品版の購入の決済をするためのリンクを取得します。"
        return "{}?client_reference_id={}".format(
            self.payment_links[period_mode],
            self.app.ctx.chiper.encrypt(
                f"{user_id}_{guild_id}_{period_mode}_{int(time())}"
            )
        )