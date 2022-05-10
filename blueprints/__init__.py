# RT - Blueprints

from sanic.request import Request
from sanic import Blueprint

from data import API_HOST


bp = Blueprint("normal", host=API_HOST)