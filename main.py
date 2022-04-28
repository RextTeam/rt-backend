# RT.Backend by Rext

from rtlib import TypedSanic, setup
from data import DATA


app = TypedSanic()
setup(app)


app.run(**DATA["sanic"])