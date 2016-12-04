""" Entry point of Academia backend package. """
from os import unlink, environ
from code import interact
from tempfile import mkstemp
from unittest import defaultTestLoader, TextTestRunner
from importlib import import_module
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from depot.manager import DepotManager

from app.config import DB_USERNAME, DB_PASSWORD, DB_NAME, DATA_ROOT

DB_URI = "postgresql+pg8000://%s:%s@db:5432/%s" % (DB_USERNAME, DB_PASSWORD, DB_NAME)

def setup_app(app_name=__name__, db_uri=None):
    """
    Set up Flask application and database.

    Args:
        app_name: Name of the Flask application.
        db_uri: Database URI for SQLAlchemy to connected to.
    """
    global app, db
    # Flask application
    app = Flask(app_name)
    # Application configuration
    app.config.update({
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    })
    # Database object
    db = SQLAlchemy(app)
    # Depot
    DepotManager.configure("default", {
        "depot.storage_path": DATA_ROOT
    })
    app.wsgi_app = DepotManager.make_middleware(app.wsgi_app)
    # Import all related modules
    import_module("app.models")
    import_module("app.views")

def run_app(**kwargs):
    """
    Run Flask application.
    Resembles Django's "manage.py runserver" command.

    Args:
        kwargs: Keyword arguments containing backend runtime configurations.
            Usually passed from backend entry file "server.py".
    """
    global app, db
    setup_app(db_uri=DB_URI)
    # Reset database
    if kwargs.get("reset"):
        db.drop_all()
    db.create_all()
    # Run app
    app.run(
        host=kwargs.get("host"),
        port=kwargs.get("port"),
        debug=not kwargs.get("production", False)
    )

def run_test(**kwargs):
    """
    Run all tests included in "tests" module.
    Resembles Django's "manage.py test" command.

    Args:
        kwargs: Keyword arguments containing backend runtime configurations.
    """
    global db
    # Set-up in-memory application
    setup_app(db_uri="sqlite://")
    db.create_all()
    # Run tests
    tests = defaultTestLoader.loadTestsFromModule("app.tests")
    TextTestRunner().run(tests)

def run_shell(**kwargs):
    """
    Run an interactive Python shell with application and database set up.
    Resembles Django's "manage.py shell" command.

    Args:
        kwargs: Keyword arguments containing backend runtime configurations.
    """
    setup_app(db_uri=DB_URI)
    # Environment variables
    environ["TERM"] = "xterm-256color"
    # Run in interactive mode
    interact()

# Mode to handler mapping
__mode_handler_mapping = {
    "app": run_app,
    "test": run_test,
    "shell": run_shell
}

def run_with_mode(mode, **kwargs):
    """
    Run backend with mode indicated by given argument.

    Args:
        mode: Mode to run. (See "__mode_handler_mapping" for available modes)
        kwargs: Keyword arguments containing backend runtime configurations.
    """
    __mode_handler_mapping[mode](**kwargs)
