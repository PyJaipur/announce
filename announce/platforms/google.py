import string
import json
import random
import pendulum
import pickle
import os.path
from urllib.parse import urlparse, parse_qs, urlencode
from announce import const
import os
import pickle
import requests
from requests_oauthlib import OAuth1Session
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs, urlencode
from announce import const


def preprocess(event):
    return event


def auth(path):
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None
    if os.path.exists(path / "googletoken.pickle"):
        with open(path / "googletoken.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                path / "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(path / "googletoken.pickle", "wb") as token:
            pickle.dump(creds, token)
    service = build("calendar", "v3", credentials=creds)
    return service


def run(event, info):
    session = 
    if 'completed' in info:
        return info
    service = refresh_google()
    body = {
        "summary": event.title,
        "description": event.short,
        "visibility": "public",
        "start": {
            "dateTime": event.start.to_iso8601_string(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {"dateTime": event.end.to_iso8601_string(), "timeZone": "Asia/Kolkata",},
    }

    calevent = service.events().insert(calendarId="primary", body=body).execute()
    link = calevent.get("htmlLink")
    add_to_cal = "https://calendar.google.com/event?" + urlencode(
        {
            "action": "TEMPLATE",
            "tmeid": parse_qs(urlparse(link).query)["eid"][0],
            "tmsrc": const.email,
            "scp": "ALL",
        }
    )
    conf = (
        service.events()
        .patch(
            calendarId="primary",
            eventId=calevent.get("id"),
            body={
                "conferenceData": {
                    "createRequest": {
                        "requestId": f"pyj-{''.join(random.sample(string.ascii_lowercase, 10))}"
                    }
                }
            },
            sendNotifications=True,
            conferenceDataVersion=1,
        )
        .execute()
    )
    call_link = conf.get("hangoutLink")
    return const.Event(
        **{**event._asdict(), "add_to_cal": add_to_cal, "call": call_link}
    )
