""" Marshmallow schemas for serialization and deserialization. """
from hashlib import pbkdf2_hmac
from marshmallow import fields
from marshmallow_sqlalchemy import ModelSchema, field_for

from app.config import USER_PASSWD_HMAC_SALT, N_HASH_ROUNDS
from app.models import User

class UserSchema(ModelSchema):
    """ User schema class. """
    id = field_for(User, "id", dump_only=True)
    email = field_for(User, "email", validate=validate.Email())
    password = fields.Method("calc_password", required=True, load_only=True)
    join_date = field_for(User, "join_date", dump_only=True)
    def calc_password(self, raw_password):
        """ Calculate HMAC-SHA2 password. """
        return pbkdf2_hmac("sha256", raw_password, USER_PASSWD_HMAC_SALT, N_HASH_ROUNDS)
    # Meta class
    class Meta:
        model = User
