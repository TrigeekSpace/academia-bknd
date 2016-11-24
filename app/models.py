""" SQLAlchemy database models. """
from app import db

class User(db.Model):
    """ User model class. """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.Binary(32))
    join_date = db.Column(db.DateTime(), default=datetime.now)
    active = db.Column(db.Boolean(), default=False)
