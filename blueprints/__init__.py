# RT - Blueprints

from sanic import Blueprint, html

from core import Request

from .captcha import bp as captcha_bp
from .oauth import bp as oauth_bp
from .short_url import bp as short_url_bp # type: ignore
from .payments import bp as payments_bp


bp = Blueprint("general")


@bp.route("/embed")
async def short_url(request: Request):
    return html(await request.app.ctx.tempylate.aiorender_from_file(
        f"rt-frontend/pages/embed.html", data=request.args
    ))


bpg = Blueprint.group(bp, captcha_bp, oauth_bp, short_url_bp, payments_bp)