""" SQLAlchemy database models. """
from datetime import datetime

from app import db
from app.util.data import many_to_many, foreign_key

class User(db.Model):
    """ User model class. """
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.Binary(32))
    join_date = db.Column(db.DateTime(), default=datetime.now)
    active = db.Column(db.Boolean(), default=False)

class Session(db.Model):
    """ API session class. """
    token = db.Column(db.Binary(64), primary_key=True)
    user, user_id = foreign_key("User", backref_name="sessions")

class AbstractBaseGroup(object):
    """ Abstract base group class. """
    pass

class Group(db.Model, AbstractBaseGroup):
    """ Group model class. """
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), unique=True)
    users = many_to_many("Group", "User", backref_name="groups")
