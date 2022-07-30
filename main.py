# RT.Backend by Rext

from core import TypedSanic, setup

from data import DATA, TEST

from blueprints import bpg, bpg_api


app = TypedSanic("rt-backend")
setup(app)
app.blueprint(bpg)
app.blueprint(bpg_api)


DATA["sanic"].setdefault("debug", TEST)
app.run(**DATA["sanic"])
app.ctx.cachers.close()