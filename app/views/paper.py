""" Paper-related APIs. """
import os
from flask import request, jsonify, g

from app import db
from app.models import *
from app.schemas import *
from app.util.core import *
from app.util.data import *

@register_view("/papers")
class PaperView(APIView):
    """ User view class. """
    def list(self):
        """ List all users. """
        papers = filter_user(Paper.query, Paper).all()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(PaperSchema, papers, many=True)
        )

    def create(self):
        """ Create a new user. """
        # Load user data
        data = {**request.form, **request.files}
        paper = load_data(PaperSchema, data)
        # Add to database
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(PaperSchema, paper)
        )
    def retrieve(self, id):
        """ Get existing user information. """
        user = get_pk(Paper, id)
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(PaperSchema, paper)
        )
    def partial_update(self, id):
        """ Update user information. """
        # Load update data, then find and update user
        paper = get_pk(Paper, id)
        data = {**request.form, **request.files}
        load_data(PaperSchema, data, instance=paper)
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(UserSchema, user)
        )
    def destroy(self, id):
        """ Remove user. """
        # Find and remove user
        paper = get_pk(Paper, id)
        db.session.delete(paper)
        db.session.commit()
        # Success
        return jsonify(**SUCCESS_RESP)
