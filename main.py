# RT.Backend by Rext

from core import TypedSanic, setup
from data import DATA, REALHOST_PORT

from blueprints import bp


app = TypedSanic("rt-backend")
setup(app)
app.blueprint(bp)


app.run(**DATA["sanic"])
