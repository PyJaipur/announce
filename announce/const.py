import os
from collections import namedtuple


def env(key, default=None):
    val = os.environ.get(key, default)
    return val


database_url = env("DATABASE_URL")
secret = os.environ.get("BOTTLE_SECRET", "pyjdoorman")
cookie_name = "pyj"
cookie_kwargs = {"path": "/", "domain": base_domain}
base_domain = env("BASE_DOMAIN")
protocol = "https"
is_dev = base_domain is None
if is_dev:
    cookie_kwargs = {}
    base_domain = "localhost:8000"
    protocol = "http"

email = "pyjaipur.india@gmail.com"
tw = "https://api.twitter.com/1.1"
tw_upload = "https://upload.twitter.com/1.1"
format = "D MMMM YYYY HH:mm:ss Z"
Event = namedtuple(
    "Event",
    "title start end short description poster add_to_cal call tweet_id email_sent linkedin_id",
)

mailing_list_email = "pyjaipur@python.org"
linkedin_org_id = 14380746
