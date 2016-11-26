""" User-related APIs. """
from flask import request, jsonify

from app import db
from app.models import User, Session
from app.schemas import UserSchema
from app.util.core import SUCCESS_RESP, APIView, register_view, res_action
from app.util.data import load_data, dump_data, get_pk
from app.util.perm import auth_required

@register_view("/users")
class UserView(APIView):
    """ User view class. """
    schema = UserSchema()
    def create(self):
        """ Create a new user. """
        # Load user data
        user = load_data(self.schema, request.get_json())
        # Add to database
        db.session.add(user)
        db.session.commit()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(self.schema, user)
        )
    def retrieve(self, id):
        """ Get existing user information. """
        user = get_pk(User, id)
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(self.schema, user)
        )
    def partial_update(self, id):
        """ Update user information. """
        # Load update data, then find and update user
        user = get_pk(User, id)
        load_data(self.schema, request.get_json(), instance=user)
        db.session.commit()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(self.schema, user)
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
    def login(self):
        """ Log user in. """
        # TODO: User log-in
    @res_action("logout")
    @auth_required()
    def logout(self):
        """ Log user out. """
        # Remove current session
        api_session = get_pk(Session, request.headers[AUTH_TOKEN_HEADER])
        db.session.delete(api_session)
        db.session.commit()
        # Success
        return jsonify(**SUCCESS_RESP)
