import bottle
from announce import models, const
from functools import wraps


def make_render(app):
    def render(template_name, **kwargs):
        kwargs.update({"request": bottle.request, "url_for": app.get_url})
        return bottle.jinja2_template(template_name, **kwargs)

    return render


class Plugin:
    name = None
    api = 2

    def setup(self, app):
        self.app = app


class AutoSession(Plugin):
    name = "auto_session"

    def apply(self, callback, route):
        @wraps(callback)
        def wrapper(*a, **kw):
            bottle.request.session = models.Session()
            try:
                return callback(*a, **kw)
            finally:
                bottle.request.session.close()

        return wrapper


class CurrentUser(Plugin):
    name = "current_user"

    def apply(self, callback, route):
        @wraps(callback)
        def wrapper(*a, **kw):
            # Check cookies
            user = models.AnonUser()
            cook = bottle.request.get_cookie(const.cookie_name, secret=const.secret)
            if cook is not None:
                token = (
                    bottle.request.session.query(models.LoginToken)
                    .filter_by(token=cook, has_logged_out=False)
                    .first()
                )
                bottle.request.token = token
                if token is not None:
                    user = token.user
            bottle.request.user = user
            return callback(*a, **kw)

        return wrapper


class LoginRequired(Plugin):
    name = "login_required"

    def apply(self, callback, route):
        @wraps(callback)
        def wrapper(*a, **kw):
            if isinstance(bottle.request.user, models.AnonUser):
                return bottle.redirect(
                    self.app.get_url("get_login", next_url=bottle.request.url)
                )
            return callback(*a, **kw)

        return wrapper
