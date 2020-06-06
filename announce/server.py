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
def post_login(otp, Otp, User, LoginToken, Group, Member, Cred, AuditLog):
    session = bottle.request.session
    o = session.query(Otp).filter_by(otp=otp).first()
    if o is None:
        return bottle.redirect(app.get_url("get_login"))
    u = session.query(User).filter_by(tg_handle=o.tg_handle).first()
    if u is None:
        u = User(tg_handle=o.tg_handle)
        g = Group.new_group(session, creator=u, name=f"{u.tg_handle}-group")
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
    return render("dash.html")


@app.post("/newgroup", name="post_newgroup")
@fill_args
def post_newgroup(groupname, Group):
    session = bottle.request.session
    u = bottle.request.user
    Group.new_group(session, creator=u, name=groupname)
    return bottle.redirect(app.get_url("get_dashboard"))


@app.get("/group", name="get_group")
@fill_args
def get_group(groupid, Group, Cred, Member):
    session = bottle.request.session
    group = session.query(Group).filter_by(id=groupid).first()
    return render("group.html", group=group)


@app.post("/group", name="post_group")
@fill_args
def post_group(
    groupid,
    Otp,
    User,
    Member,
    Cred,
    AuditLog,
    Group,
    new_member_tghandle=None,
    new_member_otp=None,
    new_cred_name=None,
    new_cred_value=None,
):
    session = bottle.request.session
    I = bottle.request.user.tg_handle
    group = session.query(Group).filter_by(id=groupid).first()
    if group is None:
        return bottle.redirect(app.get_url("get_dashboard"))
    # add new members
    if new_member_tghandle is not None and new_member_otp is not None:
        u = session.query(User).filter_by(tg_handle=new_member_tghandle).first()
        if u is None:
            u = User(tg_handle=new_member_tghandle)
            session.add(u)
        o = session.query(Otp).filter_by(otp=new_member_otp).first()
        if u is not None and o is not None and o.tg_handle == u.tg_handle:
            session.add(Member(user_id=u.id, group_id=group.id))
            session.delete(o)
            session.add(AuditLog(text=f"{I} invited {u.tg_handle}", group_id=group.id,))
    # Add new credentials
    if new_cred_name and new_cred_value:
        session.add(Cred(name=new_cred_name, value=new_cred_value, group_id=group.id))
        session.add(AuditLog(text=f"{I} added {new_cred_name}", group_id=group.id,))
    # Update existing credentials
    for key, value in bottle.request.forms.items():
        value = value.strip()
        if key.startswith("existing_cred_") and key.endswith("_name"):
            _, _, cid, _ = key.split("_")
            c = session.query(Cred).filter_by(id=cid).first()
            if value == "":
                session.delete(c)
                session.add(AuditLog(text=f"{I} deleted {c.name}", group_id=group.id,))
            else:
                if str(c.name) != str(value):
                    session.add(
                        AuditLog(
                            text=f"{I} renamed {c.name} to {value}, group_id=group.id"
                        )
                    )
                c.name = str(value)
                var_value = str(
                    bottle.request.forms.get(f"existing_cred_{cid}_value")
                ).strip()
                if str(c.value) != str(var_value):
                    session.add(
                        AuditLog(
                            text=f"{I} changed the value of {c.name}",
                            group_id=group.id,
                        )
                    )
                c.value = var_value
    # member permissions
    for c in group.credentials:
        for m in group.memberships:
            key = f"mem_perm_{m.id}_{c.id}"
            set_on = bottle.request.forms.get(key) == "on"
            is_on = m.has_credential(c.name)
            if set_on and not is_on:
                m.allowed_creds = {**m.allowed_creds, c.name: True}
                session.add(
                    AuditLog(
                        text=f"{I} gave {m.user.tg_handle} access to {c.name}",
                        group_id=group.id,
                    )
                )
            elif not set_on and is_on:
                m.allowed_creds = {**m.allowed_creds, c.name: False}
                session.add(
                    AuditLog(
                        text=f"{I} revoke {m.user.tg_handle} access to {c.name}",
                        group_id=group.id,
                    )
                )
    session.commit()
    return bottle.redirect(app.get_url("get_group", groupid=groupid))


@app.get("/events", name="get_events")
@fill_args
def get_events(groupid, Group):
    session = bottle.request.session
    I = bottle.request.user.tg_handle
    group = session.query(Group).filter_by(id=groupid).first()
    return render("events.html", group=group)
