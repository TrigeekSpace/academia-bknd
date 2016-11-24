""" User-related APIs. """
from flask import request, session, jsonify

from app import db
from app.models import User
from app.schemas import UserSchema
from app.util import SUCCESS_RESP, APIView, register_view, res_action, load_data, dump_data, get_pk

@register_view("/users")
class UserView(APIView):
    schema = UserSchema()
    def create(self):
        """ Create a new user. """
        # Load user data
        user = load_data(self.schema, request.form)
        # Add to database
        db.session.add(user)
        db.session.commit()
        # Success
        return jsonify(dump_data(self.schema, user))
    def retrieve(self, id):
        """ Get existing user information. """
        user = get_pk(User, id)
        return jsonify(dump_data(self.schema, user))
    def partial_update(self, id):
        """ Update user information. """
        # Load update data, then find and update user
        user = get_pk(User, id)
        update_data = load_data(self.schema, request.form, partial=True)
        user.__dict__.update(**update_data)
        db.session.commit()
        # Success
        return jsonify(dump_data(self.schema, user))
    def destroy(self, id):
        """ Remove user. """
        # Find and remove user
        user = get_pk(User, id)
        db.session.delete(user)
        db.session.commit()
        # Success
        return jsonify(SUCCESS_RESP)
    @res_action("login")
    def login(self):
        """ Log user in. """
        # TODO: Log-in
        pass
    @res_action("logout")
    def logout(self):
        """ Log user out. """
        session["user"] = None
        return jsonify(SUCCESS_RESP)
