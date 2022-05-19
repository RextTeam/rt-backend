# RT - Blueprints

from sanic import Blueprint

from data import API_HOSTS


bp = Blueprint("normal", host=API_HOSTS)