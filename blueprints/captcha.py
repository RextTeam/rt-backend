# RT - Captcha

from sanic import Blueprint
from sanic.response import redirect, html

from core import Request

from data import TIMEOUT


bp = Blueprint("captcha", "/captcha")


@bp.route("/login/<guild_id>")
async def captcha(request: Request, guild_id: str):
    response = redirect(request.url_for("oauth.login"))
    response.cookies["redirect"] = f"/captcha/start/{guild_id}"
    return response


@bp.route("/start/<guild_id>")
async def start(request: Request, guild_id: str):
    return html(await request.app.ctx.tempylate.aiorender(
        "rt-frontend/pages/captcha.html", mode="start",
        guild_id=guild_id
    ))


@bp.route("/result/<guild_id:int>", methods=("GET", "POST"))
async def result(request: Request, guild_id: int):
    assert (data := await request.app.ctx.oauth.fetch_user(request)) is not None, TIMEOUT
    if (await request.app.ctx.hcaptcha.verify(
        request.form.get("h-captcha-response"))
    ).get("success", False):
        content = await request.app.ctx.ipcs.request(
            request.app.ctx.ipcs.detect_target(guild_id),
            "on_success", data["id"]
        )
    else:
        content = "Captcha failed. Please retry.\n認証に失敗しました。もう一度行なってください。"
    response = html(await request.app.ctx.tempylate.aiorender(
        "rt-frontend/pages/captcha.html", mode="result",
        content=content
    ))
    if "redirect" in request.cookies:
        del response.cookies["redirect"]
    return response