import bottle
from bottle_tools import fill_args
from importlib import import_module
from announce import plugins


app = bottle.Bottle()
app.install(plugins.AutoSession())
app.install(plugins.CurrentUser())
app.install(plugins.LoginRequired())
render = plugins.render


@app.get("/", name="get_login", skip=["login_required"])
def get_login():
    return render("login.html")


@app.post("/login", name="post_login", skip=["login_required"])
@fill_args
def post_login(otp, Otp, User, LoginToken, Group):
    o = bottle.request.session.query(Otp).filter_by(otp=otp)
    u = bottle.request.session.query(User).filter_by(tg_handle=o.tg_handle).first()
    if u is None:
        u = User(tg_handle=o.tg_handle)
        g = Group(name=o.tg_handle)
        bottle.request.session.add(u)
        bottle.request.session.add(g)
    tok = LoginToken.loop_create(bottle.request.session, user=u)
    bottle.request.session.delete(o)
    bottle.request.session.commit()
    bottle.response.set_cookie(
        const.cookie_name,
        tok.token,
        secret=const.secret,
        max_age=3600 * 24 * 60,
        **const.cookie_kwargs,
    )
    return bottle.redirect(app.get_url("get_dashboard"))


@app.get("/dash", name="get_dashboard")
def get_dashboard():
    groups = bottle.request.user.get_groups(bottle.request.session)
    return render("dash.html", groups=groups)
