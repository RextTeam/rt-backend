# RT - Short URL

from random import randint

from sanic import Blueprint
from sanic.response import redirect

from core import Request

from data import TEST, REALHOST_PORT


bp = Blueprint("short_url")


ALTERNATIVE_FOR_INVALID = (
    "https://www.youtube.com/watch?v=ESx_hy1n7HA",
    "https://www.youtube.com/watch?v=Y0EcKR05Ac4",
    "https://www.youtube.com/watch?v=LCOItseOsFE",
    "https://www.youtube.com/watch?v=7pirFsqx9H8",
    "https://youtu.be/5f-pp3OEbTI",
    "https://www.youtube.com/watch?v=9Lve8kzgdgA",
    "https://www.youtube.com/watch?v=wa2K_8Ff41M",
    "https://www.youtube.com/watch?v=5f-pp3OEbTI",
    "https://www.youtube.com/watch?v=ezME0Wy0OAE"
)
ALTERNATIVE_MAX_INDEX = len(ALTERNATIVE_FOR_INVALID) - 1


@bp.route("/<code>", host=REALHOST_PORT if TEST else "rtbo.tk")
async def short_url(request: Request, code: str):
    async with request.app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT Url FROM ShortURL WHERE Endpoint = %s;",
                (code,)
            )
            if (row := await cursor.fetchone()):
                return redirect(row[0])
    return redirect(ALTERNATIVE_FOR_INVALID[randint(0, ALTERNATIVE_MAX_INDEX)])