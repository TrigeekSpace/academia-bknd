""" Marshmallow schemas for serialization and deserialization. """
from hashlib import pbkdf2_hmac
from marshmallow import fields, validate
from marshmallow_sqlalchemy import ModelSchema, field_for

from app import db
from app.config import USER_PASSWD_HMAC_SALT, N_HASH_ROUNDS
from app.models import User

class UserSchema(ModelSchema):
    """ User schema class. """
    email = field_for(User, "email", validate=validate.Email())
    password = fields.Method("calc_password")
    def calc_password(self, raw_password):
        """
        Calculate HMAC-SHA2 password.

        Args:
            raw_password: Raw user password.
        Returns:
            Byte sequence of HMAC-SHA256 result of user password.
        """
        return pbkdf2_hmac("sha256", raw_password, USER_PASSWD_HMAC_SALT, N_HASH_ROUNDS)
    class Meta:
        """ User schema meta class. """
        model = User
        sqla_session = db.session
        load_only = ("password",)
        dump_only = ("id", "join_date")
        exclude = ("sessions",)
