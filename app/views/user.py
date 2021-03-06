""" User-related APIs. """
import os
from base64 import b64encode, b64decode
from flask import request, jsonify, g
from marshmallow import fields
from sqlalchemy.exc import ProgrammingError

from app import db
from app.models import User, Session
from app.schemas import UserSchema
from app.config import TOKEN_LEN, AUTH_TOKEN_HEADER
from app.util.core import SUCCESS_RESP, APIView, register_view, res_action, assert_logic, APIError, map_error
from app.util.data import load_data, dump_data, get_pk, get_by, parse_param, filter_user, get_data, handle_prog_error
from app.util.perm import auth_required

@register_view("/users")
class UserView(APIView):
    """ User view class. """
    def list(self):
        """ List all users. """
        users = filter_user(User.query, User).all()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(UserSchema, users, many=True, nested_user=True)
        )
    def create(self):
        """ Create a new user. """
        # Load user data
        import sys
        print(request.get_json(), file=sys.stderr)
        user = load_data(UserSchema, get_data())
        # Add to database
        with map_error({ProgrammingError: handle_prog_error}):
            db.session.add(user)
            db.session.commit()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(UserSchema, user)
        )
    def retrieve(self, id):
        """ Get existing user information. """
        user = get_pk(User, id)
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(UserSchema, user, nested_user=True)
        )
    def partial_update(self, id):
        """ Update user information. """
        # Load update data, then find and update user
        user = get_pk(User, id)
        with map_error({ProgrammingError: handle_prog_error}):
            load_data(UserSchema, get_data(), instance=user)
            db.session.commit()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(UserSchema, user)
        )
    def destroy(self, id):
        """ Remove user. """
        # Find and remove user
        user = get_pk(User, id)
        db.session.delete(user)
        db.session.commit()
        # Success
        return jsonify(**SUCCESS_RESP)
    @res_action("login")
    @parse_param(schema_class={
        "username": fields.String(),
        "password": fields.Method(deserialize="calc_password"),
        "calc_password": UserSchema.calc_password
    })
    def login(self):
        """ Log user in. """
        import sys
        print(g, file=sys.stderr)
        assert g.params!=None
        # Find user
        user = get_by(
            User,
            username=g.params["username"],
            password=g.params["password"],
            error=APIError(401, "incorrect_credential")
        )
        # Log user in
        session = Session(token=os.urandom(TOKEN_LEN), user=user)
        db.session.add(session)
        db.session.commit()
        # Token
        token = b64encode(session.token).decode()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            user=dump_data(UserSchema, user),
            token=token
        )
    @res_action("logout")
    @auth_required()
    def logout(self):
        """ Log user out. """
        # Remove current session
        with map_error(APIError(400, "bad_token")):
            api_session = get_by(Session, b64decode(request.headers[AUTH_TOKEN_HEADER]))
            db.session.delete(api_session)
            db.session.commit()
        # Success
        return jsonify(**SUCCESS_RESP)
