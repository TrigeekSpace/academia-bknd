""" Entry point of Academia backend package. """
from os import unlink
from code import interact
from tempfile import mkstemp
from unittest import defaultTestLoader, TextTestRunner
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.config import DB_USERNAME, DB_PASSWORD, DB_NAME

DB_URI = "postgresql+pg8000://%s:%s@db:5432/%s" % (DB_USERNAME, DB_PASSWORD, DB_NAME)

def setup_app(app_name=__name__, db_uri=None):
    """ Set up application and database. """
    global app, db
    # Flask application
    app = Flask(app_name)
    # Database object
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    db = SQLAlchemy(app)
    # Import all related modules
    import app.models
    import app.views

def run_app(**kwargs):
    """ Run application. """
    global app
    setup_app(db_uri=DB_URI)
    # Run app
    app.run(
        host=kwargs.get("host"),
        port=kwargs.get("port"),
        debug=not kwargs.get("production")
    )

def run_test(**kwargs):
    """ Run in test mode. """
    global db
    # Make temporary database and set up application
    db_file = mkstemp(prefix="academia-test-", suffix=".db")
    setup_app(db_uri="sqlite://%s" % db_file)
    db.create_all()
    # Run tests
    tests = defaultTestLoader.loadTestsFromModule("app.tests")
    TextTestRunner().run(tests)
    # Unlink database
    unlink(db_file)

def run_shell(**kwargs):
    """ Run in shell mode. """
    setup_app(db_uri=DB_URI)
    # Run in interactive mode
    interact()

# Mode to handler mapping
__mode_handler_mapping = {
    "app": run_app,
    "test": run_test,
    "shell": run_shell
}

def run_with_mode(mode, **kwargs):
    """ Run with given mode. """
    __mode_handler_mapping[mode](**kwargs)
