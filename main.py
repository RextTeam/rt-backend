# RT.Backend by Rext

from core import TypedSanic, setup

from data import DATA, TEST

from blueprints import bpg


app = TypedSanic("rt-backend")
setup(app)
app.blueprint(bpg)


DATA["sanic"].setdefault("debug", TEST)
app.run(**DATA["sanic"])