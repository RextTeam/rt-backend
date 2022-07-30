# RT - OAuth

from sanic.response import redirect
from sanic import Blueprint

from core.utils import CoolDown
from core import Request, api


bp = Blueprint("oauth", "/account")
bp_api = Blueprint("oauth_api")


@bp.route("/login")
@CoolDown(1, 1)
async def login(request: Request):
    return redirect(await request.app.ctx.oauth.generate_url(
        request.url_for("oauth.callback"), ("identify",)
    ))


@bp.route("/callback")
@CoolDown(1, 1)
async def callback(request: Request):
    response = redirect(request.cookies.get("redirect", "/"))
    response.cookies["session"] = await request.app.ctx.oauth.encrypt(
        await request.app.ctx.oauth.make_cookie(
            await request.app.ctx.oauth.fetch_user(
                (await request.app.ctx.oauth.get_token(
                    request.args.get("code"), request.url_for("oauth.callback")
                ))["access_token"]
            )
        )
    )
    return response


@bp.route("/logout")
async def logout(request: Request):
    response = redirect("/")
    if "session" in response.cookies:
        del response.cookies["session"]
    return response


@bp_api.route("/account")
async def account(request: Request):
    user = await request.app.ctx.oauth.fetch_user(request)
    return api(None if user is None else user)
