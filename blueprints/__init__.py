# RT - Blueprints

from sanic import Blueprint

from .captcha import bp as captcha_bp
from .oauth import bp as oauth_bp
from .short_url import bp as short_url_bp


bpg = Blueprint.group(captcha_bp, oauth_bp, short_url_bp)