import bottle
from bottle_tools import fill_args
from importlib import import_module
from announce import plugins, const


app = bottle.Bottle()
app.install(plugins.AutoSession())
app.install(plugins.CurrentUser())
app.install(plugins.LoginRequired())
render = plugins.make_render(app)


@app.get("/", name="get_login", skip=["login_required"])
def get_login():
    if not bottle.request.user.is_anon:
        return bottle.redirect(app.get_url("get_dashboard"))
    return render("login.html")


@app.post("/login", name="post_login", skip=["login_required"])
@fill_args
def post_login(otp, Otp, User, LoginToken, Group, Member, Cred):
    session = bottle.request.session
    o = session.query(Otp).filter_by(otp=otp).first()
    if o is None:
        return bottle.redirect(app.get_url("get_login"))
    u = session.query(User).filter_by(tg_handle=o.tg_handle).first()
    if u is None:
        u = User(tg_handle=o.tg_handle)
        g = Group(name=o.tg_handle)
        session.add(u)
        session.add(g)
        session.commit()
        m = Member(user_id=u.id, group_id=g.id, allowed_creds={"all": True})
        session.add(m)
        c = Cred(name="owner", value="", group_id=g.id)
        session.add(c)
        session.commit()
    tok = LoginToken.loop_create(session, user=u)
    session.delete(o)
    session.commit()
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


@app.get("/group", name="get_group")
@fill_args
def get_group(groupid, Group, Cred, Member):
    session = bottle.request.session
    group = session.query(Group).filter_by(id=groupid).first()
    return render("group.html", group=group)


@app.post("/group", name="post_group")
@fill_args
def post_group(groupid):
    pass
