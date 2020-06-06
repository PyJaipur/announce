import bottle
from bottle_tools import fill_args
from importlib import import_module
from announce.models import Session


class AutoSession:
    name = "auto_session"
    api = 2

    def apply(self, callback, route):
        @wraps(callback)
        def wrapper(*a, **kw):
            bottle.request.session = Session()
            try:
                return callback(*a, **kw)
            finally:
                bottle.request.session.close()

        return wrapper

    def setup(self, app):
        self.app = app


app = bottle.Bottle()
app.install(AutoSession())


@app.post("/event")
def event_view(Event):
    ev = Event()
    bottle.request.session.add(ev)
    bottle.request.session.commit()
    return {"eventid": ev.id}


@app.get("/event")
@fill_args
def event_view(eventid: str, Event):
    ev = bottle.request.session.query(Event).filter_by(id=eventid)
    return {"eventid": ev.id}


@app.post("/image")
def image_view(Image):
    im = Image()
    # save and generate image path
    im.path = "."
    bottle.request.session.add(im)
    bottle.request.session.commit()
    return {"eventid": ev.id}


@app.get("/creds")
def see_creds(Cred):
    return {}


@app.post("/creds")
def update_creds(Cred):
    pass


@app.get("/action")
@fill_args
def action_list(eventid: str = None):
    actions = [
        "twitter.tweet",
        "linkedin.event",
        "google.event",
        "meetup.event",
        "telegram.announce",
        "website.card",
        "mailinglist.email",
    ]
    if eventid is not None:
        event = bottle.request.session.query(Event).filter_by(id=eventid)
        actions = [ac for ac in actions if not event.actions_done.get(action, False)]

    return {"available": actions}


@app.post("/action")
@fill_args
def action_view(
    eventid: str,
    imageid: str,
    title: str,
    start: str,
    end: str,
    description: str,
    action: str,
    Event,
    Image,
):
    key = f"announce.platforms.{action}"
    event = bottle.request.session.query(Event).filter_by(id=eventid)
    if event.actions_done.get(key, False):
        return {"reason": "Action already done."}
    im = (
        bottle.request.session.query(Image).filter_by(id=imageid)
        if imageid is not None
        else None
    )
    fn = import_module(key)
    fn(
        event=event,
        title=title,
        start=start,
        end=end,
        description=description,
        image=im,
    )
    ev.actions_done[key] = True
    bottle.request.session.commit()
    return {}
