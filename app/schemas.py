""" Marshmallow schemas for serialization and deserialization. """
from hashlib import pbkdf2_hmac
from marshmallow import fields, validate
from marshmallow_sqlalchemy import ModelSchema, field_for

from app import db
from app.config import USER_PASSWD_HMAC_SALT, N_HASH_ROUNDS
from app.models import *
from app.util.data import Nested, FileField

class UserSchema(ModelSchema):
    """ User schema class. """
    email = field_for(User, "email", validate=validate.Email())
    password = fields.Method(deserialize="calc_password")
    papers = Nested("PaperSchema", many=True, model=Paper)
    collect_papers = Nested("PaperSchema", many=True, model=Paper)
    collect_notes = Nested("NoteSchema", many=True, model=Note)
    def calc_password(self, raw_password):
        """
        Calculate HMAC-SHA2 password.

        Args:
            raw_password: Raw user password.
        Returns:
            Byte sequence of HMAC-SHA256 result of user password.
        """
        return pbkdf2_hmac(
            "sha256",
            raw_password.encode(),
            USER_PASSWD_HMAC_SALT,
            N_HASH_ROUNDS
        )
    class Meta:
        """ User schema meta class. """
        model = User
        sqla_session = db.session
        load_only = ("password",)
        dump_only = ("id", "join_date")
        exclude = ("sessions",)

class PaperSchema(ModelSchema):
    """ Paper schema class. """
    paper_file = FileField()
    owners = Nested("UserSchema", many=True, model=User)
    notes = Nested("NoteSchema", many=True, model=Note)
    collectors = Nested("UserSchema", many=True, model=User)
    class Meta:
        """ User schema meta class. """
        model = Paper
        sqla_session = db.session
        load_only = () #deserialize
        dump_only = ("owners", "owngroup", "id") #serialize
        exclude = () #both not

class NoteSchema(ModelSchema):
    """ Paper schema class. """
    annotation_file = FileField()
    author = Nested("UserSchema", model=User)
    paper = Nested("PaperSchema", model=Paper)
    collectors = Nested("UserSchema", many=True, model=User)
    class Meta:
        """ User schema meta class. """
        model = Note
        sqla_session = db.session
        load_only = () #deserialize
        dump_only = ("id", "collectors", "owngroup") #serialize
        exclude = () #both not
