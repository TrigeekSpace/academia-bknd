#! /usr/bin/env python3.5
""" Entry point of Academia application. """
# Gevent monkey patch
from gevent import monkey
monkey.patch_all()

from argparse import ArgumentParser
import app

# Interactive session
if __name__=="__main__":
    # Build argument parser
    parser = ArgumentParser(description="Backend of the Academia service.")
    parser.add_argument("-H", "--host", default="0.0.0.0", help="IP address for listening.")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Port for listening.")
    parser.add_argument("-t", "--test", action="store_const", dest="mode", const="test", help="Test mode.")
    parser.add_argument("-P", "--production", action="store_true", help="Production mode.")
    parser.add_argument("-s", "--shell", action="store_const", dest="mode", const="shell", help="Interactive mode.")
    parser.add_argument("-r", "--reset", action="store_true", help="Reset database.")
    # Parse arguments
    args = vars(parser.parse_args())
    if not args.get("mode"):
        args["mode"] = "app"
    app.run_with_mode(**args)
# Production mode; get WSGI application
else:
    app.setup_app(db_uri=app.DB_URI)
    wsgi_app = app.app
