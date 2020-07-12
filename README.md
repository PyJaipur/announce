Announce
========

[![master](https://img.shields.io/badge/heroku-Master%20branch-green)](https://announce-pyj.herokuapp.com)

## Features

- login with telegram
- Create a new group
- Add events to the group
- Perform actions on multiple platforms


## Local dev

Create a `.secret` folder. Add `env` to it:

```
export TWITTER_CONSUMER_KEY=xxx
export TWITTER_CONSUMER_SECRET=xxx
export GOOGLE_CLIENT_ID=xxx
export GOOGLE_CLIENT_SECRET=xxx
export GMAIL_PWD=xxx
export LINKEDIN_CLIENT_ID=xxx
export LINKEDIN_CLIENT_SECRET=xxx
export MEETUP_CLIENT_ID=xxx
export MEETUP_CLIENT_SECRET=xxx
export TG_TOKEN=xxx
```

- Then do `docker-compose up web pgsql`.
- To create an otp for development, `docker-compose exec web python -m announce run --fn hello`.
