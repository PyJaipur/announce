import argparse

parser = argparse.ArgumentParser()
parser.add_argument("cmd", choices=("server", "bot"))
parser.add_argument("--port", type=int, default=8080)

args = parser.parse_args()

if args.cmd == "server":
    from announce.server import app

    app.run(port=args.port, host="0.0.0.0", debug=True)
elif args.cmd == "bot":
    from announce.bot import run

    run()
