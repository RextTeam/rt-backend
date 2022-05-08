# RT - OAuth

from sanic.response import redirect
from sanic import Blueprint

from core import Request, api

from data import REALHOST_PORT


bp = Blueprint("oauth", "/account")


@bp.route("/login")
async def login(request: Request):
    return redirect(await request.app.ctx.oauth.generate_url(
        request.url_for("oauth.callback"), ("identify",)
    ))


@bp.route("/callback")
async def callback(request: Request):
    assert request.conn_info is not None, "conn_infoが見つかりませんでした。"
    response = redirect(getattr(request.conn_info.ctx, "redirect", "/"))
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


@bp.route("/fetch", host=f"api.{REALHOST_PORT}")
async def account(request: Request):
    user = await request.app.ctx.oauth.fetch_user(request)
    return api(None if user is None else user)