# RT.Backend by Rext

from core import TypedSanic, setup
from data import DATA

from blueprints import bpg


app = TypedSanic("rt-backend")
setup(app)
app.blueprint(bpg)


app.run(**DATA["sanic"])