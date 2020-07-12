import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("cmd", choices=("server", "bot", "run"))
parser.add_argument("--port", type=int, default=int(os.environ.get("PORT")))
parser.add_argument("--fn", type=str, default=None)

args = parser.parse_args()

if args.cmd == "server":
    from announce.server import app

    app.run(port=args.port, host="0.0.0.0", debug=True, server="gunicorn", workers=1)
elif args.cmd == "bot":
    from announce.bot import run

    run()
elif args.cmd == "run":
    from announce.housekeeping import handle

    handle(args)
