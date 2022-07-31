# RT - Payments

from sanic import Blueprint, HTTPResponse
from sanic.response import redirect

from core import Request, TypedSanic
from core.customer_manager import PeriodMode, PaymentLinkContainer
from core.utils import api

from data import NORMAL_PAYMENT_LINKS


bp_api = Blueprint("payments_api", "/payment")
bp = Blueprint("payments")


@bp.before_server_start
async def before_server_start(app: TypedSanic, _):
    global payment_links
    payment_links = PaymentLinkContainer(app, NORMAL_PAYMENT_LINKS)


@bp_api.route("/link/<period>/<user_id:int>/<guild_id:int>")
async def get_link(_, period: PeriodMode, user_id: int, guild_id: int) -> HTTPResponse:
    return api(payment_links.get_link(period, user_id, guild_id))


@bp.route("/payment/<period>/<user_id:int>/<guild_id:int>")
async def redirect_url(_, period: PeriodMode, user_id: int, guild_id: int) -> HTTPResponse:
    response = redirect("/account/login")
    response.cookies["redirect"] = payment_links.get_link(period, user_id, guild_id)
    return response