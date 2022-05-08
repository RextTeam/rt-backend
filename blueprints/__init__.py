# RT - Blueprints

from sanic.request import Request
from sanic import Blueprint

from data import REALHOST_PORT

from core.utils import api


bp = Blueprint("normal", host=f"api.{REALHOST_PORT}")