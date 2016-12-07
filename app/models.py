""" SQLAlchemy database models. """
from datetime import datetime
from depot.fields.sqlalchemy import UploadedFileField

from app import db
from app.util.data import many_to_many, foreign_key
from app.config import TOKEN_LEN

class User(db.Model):
    """ User model class. """
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.Binary(32))
    join_date = db.Column(db.DateTime(), default=datetime.now)
    active = db.Column(db.Boolean(), default=False)
    #avatar = db.Column(UploadedFileField())
    self_introduction = db.Column(db.Text(), unique=True)
    job = db.Column(db.String(64), unique=True)

class Session(db.Model):
    """ API session class. """
    token = db.Column(db.Binary(TOKEN_LEN), primary_key=True)
    user, user_id = foreign_key("User", backref_name="sessions")

class AbstractBaseGroup(object):
    """ Abstract base group class. """
    pass

class Group(db.Model, AbstractBaseGroup):
    """ Group model class. """
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), unique=True)
    users = many_to_many("Group", "User", backref_name="groups")
    introduction = db.Column(db.Text())

class Paper(db.Model):
    """ Paper model class. """
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    title = db.Column(db.String(256), unique=False)
    abstract = db.Column(db.Text(), unique=False)
    authors = db.Column(db.String(256), unique=False)
    conference = db.Column(db.String(128), unique=False)
    publish_date = db.Column(db.DateTime(), default=datetime.now) # Accurate to the day
    owners = many_to_many("Paper", "User", backref_name="papers")
    owngroup = many_to_many("Paper", "Group", backref_name="papers")
    paper_file = db.Column(UploadedFileField())

class Note(db.Model):
    """ User model class. """
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    title = db.Column(db.String(256), unique=False)
    create_time = db.Column(db.DateTime(), default=datetime.now)
    last_modified = db.Column(db.DateTime(), default=datetime.now)
    author, author_id = foreign_key("User", backref_name="notes")
    paper, paper_id = foreign_key("Paper", backref_name="notes")
    collectors = many_to_many("Note", "User", backref_name="collect_notes")
    owngroup = many_to_many("Note", "Group", backref_name="notes")
    content = db.Column(db.Text(), unique=False)
    annotation_file = db.Column(UploadedFileField())

class Question(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    provider, provider_id = foreign_key("User", backref_name="questions_asked")
    titie = db.Column(db.String(256), unique=False)
    description = db.Column(db.Text(), unique=False)
    upvotes = many_to_many("Question", "User", backref_name="questions_upvote")
    downvotes = many_to_many("Question", "User", backref_name="questions_downvote")
    create_time = db.Column(db.DateTime(), default=datetime.now)
    last_modified = db.Column(db.DateTime(), default=datetime.now)

class Reply(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    provider, provider_id = foreign_key("User", backref_name="replies")
    host_question, q_id = foreign_key("Question", backref_name="replies")
    content = db.Column(db.Text())
    upvotes = many_to_many("Reply", "User", backref_name="replies_upvote")
    downvotes = many_to_many("Reply", "User", backref_name="replies_downvote")
    create_time = db.Column(db.DateTime(), default=datetime.now)
    last_modified = db.Column(db.DateTime(), default=datetime.now)

class Comment(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    provider, provider_id = foreign_key("User", backref_name="comments")
    host_question, q_id = foreign_key("Question", backref_name="comments")
    host_reply, r_id = foreign_key("Reply", backref_name="comments")
    content = db.Column(db.Text(), unique=False)
    create_time = db.Column(db.DateTime(), default=datetime.now)
    last_modified = db.Column(db.DateTime(), default=datetime.now)
