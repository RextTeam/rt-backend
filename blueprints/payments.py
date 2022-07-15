# RT - Payments

from sanic import Blueprint, HTTPResponse

from core import Request, TypedSanic
from core.customer_manager import PeriodMode, PaymentLinkContainer
from core.utils import api

from data import API_HOSTS, NORMAL_PAYMENT_LINKS


bp = Blueprint("payments", "/payments", API_HOSTS)


@bp.before_server_start
async def before_server_start(app: TypedSanic, _):
    global payment_links
    payment_links = PaymentLinkContainer(app, NORMAL_PAYMENT_LINKS)


@bp.route("/link/<user_id:int>/<guild_id:int>/<period>")
async def get_link(_: Request, user_id: int, guild_id: int, period: PeriodMode) -> HTTPResponse:
    return api(payment_links.get_link(period, user_id, guild_id))