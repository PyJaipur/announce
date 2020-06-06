import bottle
import pendulum
from collections import namedtuple
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
        session.add(u)
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


@app.post("/events", name="post_events")
@fill_args
def post_events(groupid, title, Group, Event, AuditLog):
    session = bottle.request.session
    I = bottle.request.user.tg_handle
    g = session.query(Group).filter_by(id=groupid).first()
    ev = Event(group_id=g.id, title=title)
    session.add(ev)
    session.add(AuditLog(text=f"{I} created event `{title}`", group_id=g.id))
    session.commit()
    return bottle.redirect(app.get_url("get_events", groupid=groupid))


@app.get("/event", name="get_event")
@fill_args
def get_event(eventid, Event):
    session = bottle.request.session
    event = session.query(Event).filter_by(id=eventid).first()
    if event is None:
        return bottle.redirect(app.get_url("get_dashboard"))
    return render("event.html", event=event, actions=const.actions)


@app.post("/event", name="post_event")
@fill_args
def post_event(eventid, title, date, start, end, description, image_url, Event):
    session = bottle.request.session
    event = session.query(Event).filter_by(id=eventid).first()
    if event is None:
        return bottle.redirect(app.get_url("get_dashboard"))
    event.title = title
    event.start = pendulum.parse(f"{date} {start}", tz="Asia/Kolkata")
    event.end = pendulum.parse(f"{date} {end}", tz="Asia/Kolkata")
    event.description = description
    event.image_url = image_url
    session.commit()
    return bottle.redirect(app.get_url("get_event", eventid=eventid))


@app.get("/action", name="get_action")
@fill_args
def get_action(eventid, action, Event):
    session = bottle.request.session
    event = session.query(Event).filter_by(id=eventid).first()
    if event is None:
        return bottle.redirect(app.get_url("get_dashboard"))
    event = event.freeze()
    mod = import_module(action)
    event = mod.preprocess(event)
    return render("action.html", event=event, action=action)


@app.post("/action", name="post_action")
@fill_args
def post_action(eventid, action, Event, AuditLog):
    session = bottle.request.session
    event = session.query(Event).filter_by(id=eventid).first()
    if event is None:
        return bottle.redirect(app.get_url("get_dashboard"))
    f_event = event.freeze()
    mod = import_module(f_action)
    event = mod.preprocess(f_event)
    updated_info = mod.run(f_event, bottle.request.user)
    inf = event.freeze().actions_info
    inf.update(updated_info)
    event.actions_info = inf
    session.add(
        AuditLog(text=f"{I} ran {action} for {event.id}", group_id=event.group_id)
    )
    session.commit()
    return bottle.redirect(app.get_url("get_event", eventid=eventid))
