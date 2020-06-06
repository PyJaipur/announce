import os
from collections import namedtuple


def env(key, default=None):
    val = os.environ.get(key, default)
    return val


base_domain = env("BASE_DOMAIN")
database_url = env("DATABASE_URL")
secret = os.environ.get("BOTTLE_SECRET", "pyjdoorman")
print(database_url)
cookie_name = "pyj"
cookie_kwargs = {"path": "/", "domain": base_domain}
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
mailing_list_email = "pyjaipur@python.org"
linkedin_org_id = 14380746
Ac = namedtuple("Ac", "name slug")
actions = [
    Ac("G-calendar", "announce.platforms.google"),
    Ac("Website", "announce.platforms.website"),
    Ac("Linkedin", "announce.platforms.linkedin"),
    Ac("Meetup", "announce.platforms.meetup"),
    Ac("Twitter", "announce.platforms.twitter"),
    Ac("Mailing list", "announce.platforms.mailinglist"),
    Ac("Telegram", "announce.platforms.telegram"),
]
gcalendar, *_ = actions
