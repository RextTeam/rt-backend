# RT - Help

from sanic import Blueprint, HTTPResponse

from core import Request, api
from core.utils import CoolDown, is_valid

from data import API_HOSTS


bp = Blueprint("rt-help", "/help", API_HOSTS)
data = {}


@bp.post("/update")
@is_valid
async def update_help(request: Request) -> HTTPResponse:
    global data
    request.app.ctx.data = data = request.json
    return api(None, "Ok")


@bp.get("/get/all")
@CoolDown(5, 4)
async def get(_) -> HTTPResponse:
    return api(data)


@bp.get("/get")
@CoolDown(5, 6)
async def get_categories(request) -> HTTPResponse:
    print(request.head.decode())
    return api({key: data[key][0] for key in data.keys()})


NOTFOUND_CATEGORY = api("そのカテゴリーが見つかりません。", "Error", 400)
@bp.get("/get/<category_name>")
@CoolDown(5, 6)
async def get_by_category_name(_, category_name: str) -> HTTPResponse:
    return api({key: data[category_name][1][key][0] for key in data[category_name][1].keys()}) \
        if category_name in data else NOTFOUND_CATEGORY


@bp.get("/get/<category_name>/<command_name>")
@CoolDown(5, 6)
async def get_by_command_name(_, category_name: str, command_name: str) \
        -> HTTPResponse:
    if category_name not in data:
        return NOTFOUND_CATEGORY
    return api(data[category_name][1][command_name][1]) if command_name in data[category_name][1] \
        else api("そのコマンドが見つかりませんでした。", "Error", 400)