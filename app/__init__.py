""" Entry point of Academia backend package. """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask application
app = Flask(__name__)
# Configuration
# TODO: Replace placeholder with env
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://%s:%s@db:5432/%s" % (
    USERNAME, PASSWORD, DB_NAME
)

# Database
db = SQLAlchemy(app)
